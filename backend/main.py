"""
The web server. Connects the browser to the scan engine.

ENDPOINTS
    GET  /                  the app itself (frontend/index.html)
    GET  /api/health        is the server up, and how is it configured
    GET  /api/attacks       what is in the attack library
    GET  /api/targets       the demo bots
    POST /api/scan          run a scan, streaming results as they finish

WHY /api/scan STREAMS
    A scan takes several seconds. If we waited and returned one big response,
    the demo would show a frozen screen. Instead we send one JSON object per
    line as each attack finishes, so the progress bar actually moves.
    This format is called NDJSON: newline-delimited JSON.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from uuid import uuid4

import yaml
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from . import config
from .attacks import load_library, reload_library
from .scanner import Target, detect_canary, run_scan
from .database import SessionLocal
from .models import Organization, Target as DBTarget, Scan as DBScan, Result as DBResult
from .art50check import check_art50

app = FastAPI(title="PromptGuard", version="0.1.0")


# ---------------------------------------------------------------- request bodies

class ScanRequest(BaseModel):
    """What the browser sends when you press Scan."""
    mode: str = Field(default="prompt", description="'prompt' or 'api'")
    system_prompt: str = ""
    api_url: str = ""
    api_headers: dict = Field(default_factory=dict)
    canary: str | None = None
    categories: list[str] | None = None


# ---------------------------------------------------------------------- helpers

def _load_demo_targets() -> list[dict]:
    path = config.DEMO_DIR / "targets.yaml"
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return raw.get("targets", [])


def _get_or_create_org(db: Session) -> Organization:
    """Get the default anonymous organization for MVP, or create it."""
    org = db.query(Organization).filter_by(domain="demo.local").first()
    if not org:
        org = Organization(
            id=uuid4(),
            name="Demo Organization",
            domain="demo.local",
            created_at=datetime.utcnow()
        )
        db.add(org)
        db.commit()
        db.refresh(org)
    return org


async def _save_scan_to_db(db: Session, report: dict, target_mode: str, duration_s: float):
    """Save scan results to the database."""
    try:
        # Get or create the demo organization
        org = _get_or_create_org(db)

        # Create a Target record
        db_target = DBTarget(
            id=uuid4(),
            org_id=org.id,
            name="Anonymous Target",
            system_prompt="",  # Will be filled by customer later
            canary=None,
            created_at=datetime.utcnow()
        )
        db.add(db_target)
        db.flush()  # Flush to get the target ID

        # Create a Scan record
        summary = report.get("summary", {})
        db_scan = DBScan(
            id=uuid4(),
            target_id=db_target.id,
            org_id=org.id,
            duration_s=duration_s,
            grade=summary.get("grade"),
            score=summary.get("score"),
            error_rate=report.get("error_rate", 0),
            created_at=datetime.utcnow()
        )
        db.add(db_scan)
        db.flush()  # Flush to get the scan ID

        # Create Result records for each attack result
        for result in report.get("results", []):
            db_result = DBResult(
                id=uuid4(),
                scan_id=db_scan.id,
                attack_id=result.get("attack_id", ""),
                verdict=result.get("verdict", "ERROR"),
                confidence=result.get("confidence", "likely"),
                evidence=result.get("evidence", ""),
                method=result.get("method", "unknown"),
                duration_ms=result.get("duration_ms", 0),
                created_at=datetime.utcnow()
            )
            db.add(db_result)

        db.commit()
        return db_scan.id
    except Exception as e:
        db.rollback()
        # Log the error but don't fail the scan - database save is best-effort
        print(f"ERROR: Failed to save scan to database: {e}")
        return None


# ------------------------------------------------------------------- API routes

@app.get("/api/health")
async def health():
    library = load_library()
    return {
        "status": "ok",
        "provider": config.PROVIDER,
        "config": config.summary(),
        "attacks_loaded": len(library.attacks),
    }


@app.get("/api/attacks")
async def list_attacks():
    """The library, for the UI to display before a scan runs."""
    library = load_library()
    return {
        "total": len(library.attacks),
        "categories": [
            {
                "id": cid,
                "label": meta.get("label", cid),
                "description": meta.get("description", ""),
                "count": len(library.by_category(cid)),
            }
            for cid, meta in library.categories.items()
        ],
        "attacks": [
            {
                "id": a.id,
                "category": a.category,
                "severity": a.severity,
                "message": a.message,
            }
            for a in library.attacks
        ],
    }


@app.post("/api/attacks/reload")
async def reload_attacks():
    """Re-read attacks.yaml without restarting the server."""
    library = reload_library()
    return {"status": "reloaded", "total": len(library.attacks)}


@app.get("/api/targets")
async def list_targets():
    return {"targets": _load_demo_targets()}


@app.post("/api/art50check")
async def art50_check(request: ScanRequest):
    """
    Passive Art. 50 AI Act compliance check.

    Checks if a website's chatbot discloses that it is AI (Art. 50(1) AI Act).
    No active attacks — just visits the page and looks at the widget.

    Returns findings about:
        - Widget detection
        - AI disclosure
        - Privacy link
        - Impressum (§ 5 DDG)
    """
    if not request.api_url.strip():
        raise HTTPException(400, "api_url (the website URL) is required")

    result = await check_art50(request.api_url)
    return result.dict()


@app.get("/api/scans")
async def list_scans(db: Session = Depends(lambda: SessionLocal())):
    """List all scans, most recent first."""
    scans = db.query(DBScan).order_by(DBScan.created_at.desc()).limit(100).all()
    return {
        "total": len(scans),
        "scans": [
            {
                "id": str(scan.id),
                "score": scan.score,
                "grade": scan.grade,
                "duration_s": scan.duration_s,
                "error_rate": scan.error_rate,
                "created_at": scan.created_at.isoformat(),
            }
            for scan in scans
        ]
    }


@app.get("/api/scans/{scan_id}")
async def get_scan(scan_id: str, db: Session = Depends(lambda: SessionLocal())):
    """Get a specific scan with all its results."""
    try:
        from uuid import UUID
        scan_uuid = UUID(scan_id)
    except ValueError:
        raise HTTPException(400, "Invalid scan_id format")

    scan = db.query(DBScan).filter_by(id=scan_uuid).first()
    if not scan:
        raise HTTPException(404, f"Scan {scan_id} not found")

    results = db.query(DBResult).filter_by(scan_id=scan_uuid).all()

    return {
        "scan": {
            "id": str(scan.id),
            "score": scan.score,
            "grade": scan.grade,
            "duration_s": scan.duration_s,
            "error_rate": scan.error_rate,
            "created_at": scan.created_at.isoformat(),
        },
        "results": [
            {
                "id": str(r.id),
                "attack_id": r.attack_id,
                "verdict": r.verdict,
                "confidence": r.confidence,
                "evidence": r.evidence,
                "method": r.method,
                "duration_ms": r.duration_ms,
            }
            for r in results
        ]
    }


@app.post("/api/scan")
async def scan(request: ScanRequest):
    """
    Run a scan and stream results as NDJSON.

    Event types sent:
        {"type": "start",    "total": 21}
        {"type": "result",   "done": 3, "total": 21, "result": {...}}
        {"type": "complete", "report": {...}, "scan_id": "..."}
        {"type": "error",    "message": "..."}
    """
    if request.mode == "prompt" and not request.system_prompt.strip():
        raise HTTPException(400, "system_prompt is required in prompt mode")
    if request.mode == "api" and not request.api_url.strip():
        raise HTTPException(400, "api_url is required in api mode")

    # If the caller did not tell us the secret, try to find it ourselves.
    # Without a canary, layer 1 of the judge cannot run at all.
    canary = request.canary or detect_canary(request.system_prompt)

    target = Target(
        mode=request.mode,
        system_prompt=request.system_prompt,
        api_url=request.api_url,
        api_headers=request.api_headers,
        canary=canary,
    )

    # The scan pushes results into this queue; the response reads from it.
    queue: asyncio.Queue = asyncio.Queue()
    report_holder = {}  # Temporary storage for the report

    async def on_result(result, done, total):
        await queue.put({"type": "result", "done": done, "total": total, "result": result})

    async def worker():
        try:
            report = await run_scan(target, request.categories, on_result)
            report_holder["report"] = report
            await queue.put({"type": "complete", "report": report})
        except Exception as e:
            await queue.put({"type": "error", "message": str(e)})
        finally:
            await queue.put(None)  # sentinel: nothing more is coming

    async def stream():
        library = load_library()
        selected = library.attacks
        if request.categories:
            selected = [a for a in selected if a.category in request.categories]
        yield json.dumps({"type": "start", "total": len(selected)}) + "\n"

        task = asyncio.create_task(worker())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield json.dumps(event) + "\n"
        finally:
            if not task.done():
                task.cancel()

            # After streaming is complete, save to database
            if "report" in report_holder:
                db = SessionLocal()
                try:
                    report = report_holder["report"]
                    await _save_scan_to_db(db, report, request.mode, report.get("duration_s", 0))
                finally:
                    db.close()

    return StreamingResponse(stream(), media_type="application/x-ndjson")


# ------------------------------------------------------------------- the frontend
# Mounted last, so it never shadows the /api routes above.

@app.get("/")
async def index():
    page = config.FRONTEND_DIR / "index.html"
    if not page.exists():
        return {"message": "Frontend not built yet. API is at /api/health"}
    return FileResponse(page)


if config.FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=config.FRONTEND_DIR), name="static")
