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

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import config
from .attacks import load_library, reload_library
from .scanner import Target, detect_canary, run_scan

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


@app.post("/api/scan")
async def scan(request: ScanRequest):
    """
    Run a scan and stream results as NDJSON.

    Event types sent:
        {"type": "start",    "total": 21}
        {"type": "result",   "done": 3, "total": 21, "result": {...}}
        {"type": "complete", "report": {...}}
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

    async def on_result(result, done, total):
        await queue.put({"type": "result", "done": done, "total": total, "result": result})

    async def worker():
        try:
            report = await run_scan(target, request.categories, on_result)
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
