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
from urllib.parse import urlparse
from uuid import uuid4, UUID

import yaml
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from . import config
from .attacks import load_library, reload_library
from .scanner import Target, detect_canary, run_scan
from .database import SessionLocal, get_db
from .models import Organization, Target as DBTarget, Scan as DBScan, Result as DBResult
from .art50check import check_art50
from .ownership import create_challenge, verify_ownership, is_domain_verified
from .apikeys import (
    create_api_key, list_api_keys, revoke_api_key, resolve_org_from_api_key,
)

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
    # Required for mode="api": whose ownership-verified domain this is.
    # Not needed for mode="prompt" — that only tests a copy of text the
    # caller submitted themselves, never a live third-party endpoint.
    org_id: str | None = None


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


async def _save_scan_to_db(db: Session, request: "ScanRequest", report: dict,
                            duration_s: float, effective_org_id: UUID | None):
    """Save scan results to the database, using the real request data."""
    try:
        # effective_org_id is resolved once in scan(): the API key's org
        # takes priority over a body org_id, which takes priority over
        # nothing at all (anonymous mode="prompt" falls back to the demo org).
        org = db.query(Organization).filter_by(id=effective_org_id).first() if effective_org_id else None
        if org is None:
            org = _get_or_create_org(db)

        # Create a Target record with what was actually submitted —
        # not a placeholder. system_prompt is a customer trade secret
        # (PLAYBOOK decision #5); retention defaults to 'delete_after_scan'
        # on the model, no override here yet since there is no UI for it.
        target_name = request.api_url or "Prompt-based target"
        db_target = DBTarget(
            id=uuid4(),
            org_id=org.id,
            name=target_name[:255],
            system_prompt=request.system_prompt,
            canary=report.get("canary"),  # explicit or auto-detected — see scanner.run_scan
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
            library_version=report.get("library_version", "1.0"),
            duration_s=duration_s,
            status="incomplete" if summary.get("incomplete") else "done",
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
                judge_reason=result.get("reason", ""),
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


class OwnershipChallengeRequest(BaseModel):
    """Request to generate ownership verification challenge."""
    org_id: str
    domain: str


class OwnershipVerifyRequest(BaseModel):
    """Request to verify ownership."""
    org_id: str
    domain: str
    token: str


class OrganizationCreateRequest(BaseModel):
    """Request to create an organization."""
    name: str
    domain: str


class OrganizationMemberRequest(BaseModel):
    """Request to add a member to an organization."""
    user_id: str
    role: str  # "owner", "admin", or "member"


@app.post("/api/ownership/challenge")
async def ownership_challenge(request: OwnershipChallengeRequest, db: Session = Depends(get_db)):
    """
    Generate a DNS verification challenge, tied to one organization + domain.

    Returns: token and instructions for DNS TXT record.

    User adds: _llmantis.{domain} TXT {token}
    Then calls /api/ownership/verify to confirm. Verified records are what
    /api/scan checks before allowing an active (mode="api") scan on that domain.
    """
    try:
        org_uuid = UUID(request.org_id)
    except ValueError:
        raise HTTPException(400, "Invalid org_id format")

    if not db.query(Organization).filter_by(id=org_uuid).first():
        raise HTTPException(404, f"Organization {request.org_id} not found")

    result = await create_challenge(db, org_uuid, request.domain)
    return result.dict()


@app.post("/api/ownership/verify")
async def ownership_verify(request: OwnershipVerifyRequest, db: Session = Depends(get_db)):
    """
    Verify ownership by checking DNS TXT record against a pending challenge.

    Looks for: _llmantis.{domain} TXT {token}

    Returns: {"verified": true/false, "verified_at": "...", "error": "..."}
    """
    try:
        org_uuid = UUID(request.org_id)
    except ValueError:
        raise HTTPException(400, "Invalid org_id format")

    result = await verify_ownership(db, org_uuid, request.domain, request.token)
    return result.dict()


# ---------------------------------------------------------------- ORGANIZATIONS


@app.post("/api/organizations")
async def create_organization(request: OrganizationCreateRequest, db: Session = Depends(get_db)):
    """
    Create a new organization.

    Returns: {"id": "...", "name": "...", "domain": "...", "created_at": "..."}
    """
    org = Organization(
        id=uuid4(),
        name=request.name,
        domain=request.domain,
        created_at=datetime.utcnow()
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    return {
        "id": str(org.id),
        "name": org.name,
        "domain": org.domain,
        "created_at": org.created_at.isoformat(),
    }


@app.get("/api/organizations")
async def list_organizations(db: Session = Depends(get_db)):
    """
    List all organizations.

    Returns: {"total": N, "organizations": [...]}
    """
    orgs = db.query(Organization).all()
    return {
        "total": len(orgs),
        "organizations": [
            {
                "id": str(o.id),
                "name": o.name,
                "domain": o.domain,
                "created_at": o.created_at.isoformat(),
            }
            for o in orgs
        ]
    }


@app.get("/api/organizations/{org_id}")
async def get_organization(org_id: str, db: Session = Depends(get_db)):
    """
    Get organization details with members and scans.

    Returns: {"id": "...", "name": "...", "members": [...], "scans": [...]}
    """
    try:
        org_uuid = UUID(org_id)
    except ValueError:
        raise HTTPException(400, "Invalid org_id format")

    org = db.query(Organization).filter_by(id=org_uuid).first()
    if not org:
        raise HTTPException(404, f"Organization {org_id} not found")

    scans = db.query(DBScan).filter_by(org_id=org_uuid).all()

    return {
        "id": str(org.id),
        "name": org.name,
        "domain": org.domain,
        "created_at": org.created_at.isoformat(),
        "scans": [
            {
                "id": str(s.id),
                "score": s.score,
                "grade": s.grade,
                "library_version": s.library_version,
                "created_at": s.created_at.isoformat(),
            }
            for s in scans
        ]
    }


class ApiKeyCreateRequest(BaseModel):
    """Request to create an API key."""
    org_id: str
    name: str


@app.post("/api/keys")
async def create_key(request: ApiKeyCreateRequest, db: Session = Depends(get_db)):
    """
    Create a new API key for an organization.

    Returns the plaintext key ONCE — it is never shown or recoverable
    again after this response. Store it now; to rotate, revoke this one
    and create a new one.
    """
    try:
        org_uuid = UUID(request.org_id)
    except ValueError:
        raise HTTPException(400, "Invalid org_id format")

    if not db.query(Organization).filter_by(id=org_uuid).first():
        raise HTTPException(404, f"Organization {request.org_id} not found")
    if not request.name.strip():
        raise HTTPException(400, "name is required")

    result = create_api_key(db, org_uuid, request.name.strip())
    return result.dict()


@app.get("/api/keys")
async def get_keys(org_id: str, db: Session = Depends(get_db)):
    """
    List an organization's API keys — never the plaintext or the hash,
    only enough to tell them apart (name, prefix, last used, revoked).
    """
    try:
        org_uuid = UUID(org_id)
    except ValueError:
        raise HTTPException(400, "Invalid org_id format")

    keys = list_api_keys(db, org_uuid)
    return {"total": len(keys), "keys": [k.dict() for k in keys]}


@app.delete("/api/keys/{key_id}")
async def delete_key(key_id: str, org_id: str, db: Session = Depends(get_db)):
    """Revoke an API key. Soft delete — the row stays, revoked_at is set."""
    try:
        key_uuid = UUID(key_id)
        org_uuid = UUID(org_id)
    except ValueError:
        raise HTTPException(400, "Invalid id format")

    if not revoke_api_key(db, key_uuid, org_uuid):
        raise HTTPException(404, "API key not found for this organization")
    return {"revoked": True}


@app.get("/api/scans")
async def list_scans(db: Session = Depends(get_db)):
    """List all scans, most recent first."""
    scans = db.query(DBScan).order_by(DBScan.created_at.desc()).limit(100).all()
    return {
        "total": len(scans),
        "scans": [
            {
                "id": str(scan.id),
                "status": scan.status,
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
async def get_scan(scan_id: str, db: Session = Depends(get_db)):
    """Get a specific scan with all its results."""
    try:
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
            "status": scan.status,
            "library_version": scan.library_version,
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
                "judge_reason": r.judge_reason,
                "method": r.method,
                "duration_ms": r.duration_ms,
            }
            for r in results
        ]
    }


@app.post("/api/scan")
async def scan(request: ScanRequest, db: Session = Depends(get_db),
                api_key_org: UUID | None = Depends(resolve_org_from_api_key)):
    """
    Run a scan and stream results as NDJSON.

    Event types sent:
        {"type": "start",    "total": 21}
        {"type": "result",   "done": 3, "total": 21, "result": {...}}
        {"type": "complete", "report": {...}, "scan_id": "..."}
        {"type": "error",    "message": "..."}

    ORGANIZATION RESOLUTION
        An X-API-Key header (if valid) always wins — that is how a CI/CD
        pipeline gets its scans attributed without knowing its own org_id.
        Otherwise we use body.org_id if given, and only fall back to the
        anonymous demo org for an unidentified mode="prompt" call.
    """
    if request.mode == "prompt" and not request.system_prompt.strip():
        raise HTTPException(400, "system_prompt is required in prompt mode")
    if request.mode == "api" and not request.api_url.strip():
        raise HTTPException(400, "api_url is required in api mode")

    effective_org_id: UUID | None = api_key_org
    if effective_org_id is None and request.org_id:
        try:
            effective_org_id = UUID(request.org_id)
        except ValueError:
            raise HTTPException(400, "Invalid org_id format")

    # PLAYBOOK §5: active attacks (mode="api") against a real endpoint
    # require verified ownership of that domain. mode="prompt" is exempt —
    # it only replays text the caller submitted themselves, never a live
    # third-party system.
    if request.mode == "api":
        if effective_org_id is None:
            raise HTTPException(
                403,
                "An org_id (or a valid X-API-Key) is required for mode='api'. "
                "Verify ownership of the target domain first via "
                "/api/ownership/challenge and /api/ownership/verify."
            )

        domain = urlparse(request.api_url).netloc or request.api_url
        if not is_domain_verified(db, effective_org_id, domain):
            raise HTTPException(
                403,
                f"Ownership of '{domain}' is not verified for this organization. "
                f"Active attacks are blocked until verification completes "
                f"(POST /api/ownership/challenge, then /api/ownership/verify)."
            )

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
                    await _save_scan_to_db(db, request, report, report.get("duration_s", 0), effective_org_id)
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
