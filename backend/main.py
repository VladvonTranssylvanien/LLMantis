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

# NOTE: deliberately no `from __future__ import annotations` here.
# FastAPI's request-body detection resolves string annotations using the
# endpoint callable's own __globals__ (see get_typed_signature in
# fastapi/dependencies/utils.py). slowapi's rate-limit decorator wraps each
# endpoint in a function defined inside slowapi's own module, so with
# postponed evaluation active, FastAPI ends up resolving our Pydantic model
# names against slowapi's globals instead of this module's — every ScanRequest
# / OrganizationCreateRequest / etc. parameter came back as an unresolved
# ForwardRef and got silently treated as a query parameter instead of a body.
# Python 3.10+ supports `X | None` natively, so nothing else here needs it.

import asyncio
import json
import re
from datetime import datetime
from urllib.parse import urlparse
from uuid import uuid4, UUID

import yaml
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from . import config
from .attacks import load_library, reload_library
from .scanner import Target, detect_canary, run_scan
from .database import SessionLocal, get_db
from .models import (
    Organization, Target as DBTarget, Scan as DBScan, Result as DBResult,
    Branding, User, Membership,
)
from .art50check import check_art50
from .ownership import create_challenge, verify_ownership, is_domain_verified
from .apikeys import (
    create_api_key, list_api_keys, revoke_api_key, resolve_org_from_api_key,
)
from .auth import (
    hash_password, verify_password, create_access_token, DUMMY_HASH,
    get_current_user, get_current_user_optional, require_membership,
)

app = FastAPI(title="LLMantis", version="0.1.0")

# Rate limiting, by caller IP. WHY: /api/scan makes ~21 real Mistral API
# calls per request — unlimited access here means unlimited cost, not just
# a DoS risk. Limits below are per-IP and reset every window; an org-aware
# limit (per API key) can layer on top once authentication exists.
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


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

# -------------------------------------------------------------- AUTHENTICATION

class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@app.post("/api/auth/register")
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterRequest, db: Session = Depends(get_db)):
    """
    Create an account. Does not create an organization — POST /api/organizations
    does that, and requires being logged in first.
    """
    email = body.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(400, "A valid email is required")
    if len(body.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(409, "An account with this email already exists")

    user = User(id=uuid4(), email=email, password_hash=hash_password(body.password),
                created_at=datetime.utcnow())
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token).dict()


@app.post("/api/auth/login")
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    """Verify email + password, return a bearer token valid for JWT_EXPIRE_HOURS."""
    email = body.email.strip().lower()
    user = db.query(User).filter_by(email=email).first()

    # Run bcrypt unconditionally, even for a nonexistent email (against a
    # fixed dummy hash) - otherwise this short-circuits before bcrypt runs,
    # and a nonexistent-email response returns in ~1/20th the time a real
    # wrong-password check takes, letting a timing measurement enumerate
    # registered emails despite the identical error message below.
    password_hash = user.password_hash if user else DUMMY_HASH
    password_ok = verify_password(body.password, password_hash)

    if not user or not password_ok:
        raise HTTPException(401, "Invalid email or password")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token).dict()


@app.get("/api/auth/me")
async def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Who am I, and which organizations do I belong to."""
    memberships = db.query(Membership).filter_by(user_id=current_user.id).all()
    orgs = []
    for m in memberships:
        org = db.query(Organization).filter_by(id=m.org_id).first()
        if org:
            orgs.append({"org_id": str(org.id), "name": org.name, "role": m.role})

    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "organizations": orgs,
    }


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
@limiter.limit("20/minute")
async def art50_check(request: Request, body: ScanRequest):
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
    if not body.api_url.strip():
        raise HTTPException(400, "api_url (the website URL) is required")

    result = await check_art50(body.api_url)
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
@limiter.limit("10/minute")
async def ownership_challenge(request: Request, body: OwnershipChallengeRequest, db: Session = Depends(get_db),
                               current_user: User = Depends(get_current_user)):
    """
    Generate a DNS verification challenge, tied to one organization + domain.
    Requires membership in that organization.

    Returns: token and instructions for DNS TXT record.

    User adds: _llmantis.{domain} TXT {token}
    Then calls /api/ownership/verify to confirm. Verified records are what
    /api/scan checks before allowing an active (mode="api") scan on that domain.
    """
    try:
        org_uuid = UUID(body.org_id)
    except ValueError:
        raise HTTPException(400, "Invalid org_id format")

    require_membership(db, current_user, org_uuid)

    if not db.query(Organization).filter_by(id=org_uuid).first():
        raise HTTPException(404, f"Organization {body.org_id} not found")

    result = await create_challenge(db, org_uuid, body.domain)
    return result.dict()


@app.post("/api/ownership/verify")
@limiter.limit("10/minute")
async def ownership_verify(request: Request, body: OwnershipVerifyRequest, db: Session = Depends(get_db),
                            current_user: User = Depends(get_current_user)):
    """
    Verify ownership by checking DNS TXT record against a pending challenge.
    Requires membership in that organization.

    Looks for: _llmantis.{domain} TXT {token}

    Returns: {"verified": true/false, "verified_at": "...", "error": "..."}
    """
    try:
        org_uuid = UUID(body.org_id)
    except ValueError:
        raise HTTPException(400, "Invalid org_id format")

    require_membership(db, current_user, org_uuid)

    result = await verify_ownership(db, org_uuid, body.domain, body.token)
    return result.dict()


# ---------------------------------------------------------------- ORGANIZATIONS


@app.post("/api/organizations")
@limiter.limit("10/minute")
async def create_organization(request: Request, body: OrganizationCreateRequest, db: Session = Depends(get_db),
                               current_user: User = Depends(get_current_user)):
    """
    Create a new organization. The caller becomes its owner.

    Returns: {"id": "...", "name": "...", "domain": "...", "created_at": "..."}
    """
    org = Organization(
        id=uuid4(),
        name=body.name,
        domain=body.domain,
        created_at=datetime.utcnow()
    )
    db.add(org)
    db.flush()  # need org.id before the Membership row

    db.add(Membership(user_id=current_user.id, org_id=org.id, role="owner",
                       created_at=datetime.utcnow()))
    db.commit()
    db.refresh(org)

    return {
        "id": str(org.id),
        "name": org.name,
        "domain": org.domain,
        "created_at": org.created_at.isoformat(),
    }


@app.get("/api/organizations")
async def list_organizations(db: Session = Depends(get_db),
                              current_user: User = Depends(get_current_user)):
    """
    List organizations the caller belongs to — not every organization in
    the system. (Used to return everyone's orgs; that was the first step
    of a chain that let anyone mint an API key for any organization.)

    Returns: {"total": N, "organizations": [...]}
    """
    memberships = db.query(Membership).filter_by(user_id=current_user.id).all()
    org_ids = [m.org_id for m in memberships]
    orgs = db.query(Organization).filter(Organization.id.in_(org_ids)).all() if org_ids else []
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
async def get_organization(org_id: str, db: Session = Depends(get_db),
                           current_user: User = Depends(get_current_user)):
    """
    Get organization details with members and scans. Requires membership.

    Returns: {"id": "...", "name": "...", "members": [...], "scans": [...]}
    """
    try:
        org_uuid = UUID(org_id)
    except ValueError:
        raise HTTPException(400, "Invalid org_id format")

    require_membership(db, current_user, org_uuid)

    org = db.query(Organization).filter_by(id=org_uuid).first()
    if not org:
        raise HTTPException(404, f"Organization {org_id} not found")

    scans = db.query(DBScan).filter_by(org_id=org_uuid).all()

    return {
        "id": str(org.id),
        "name": org.name,
        "domain": org.domain,
        "created_at": org.created_at.isoformat(),
        "branding": _branding_dict(org.branding),
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


def _branding_dict(b: Branding | None) -> dict | None:
    if b is None:
        return None
    return {
        "display_name": b.display_name,
        "logo_url": b.logo_url,
        "accent_color": b.accent_color,
        "support_email": b.support_email,
        "custom_domain": b.custom_domain,
        "updated_at": b.updated_at.isoformat(),
    }


HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class BrandingRequest(BaseModel):
    """Upsert white-label settings. Every field is optional — send only
    what you want to set. Omitted fields keep their current value."""
    display_name: str | None = None
    logo_url: str | None = None
    accent_color: str | None = None
    support_email: str | None = None
    custom_domain: str | None = None


@app.put("/api/organizations/{org_id}/branding")
async def upsert_branding(org_id: str, body: BrandingRequest, db: Session = Depends(get_db),
                           current_user: User = Depends(get_current_user)):
    """
    Create or update white-label settings for an organization. Requires
    membership in that organization.

    Cosmetic only — an agency's own logo, name and accent color on the
    Pruefbericht and report UI. Nothing here changes how a scan runs.
    """
    try:
        org_uuid = UUID(org_id)
    except ValueError:
        raise HTTPException(400, "Invalid org_id format")

    require_membership(db, current_user, org_uuid)

    org = db.query(Organization).filter_by(id=org_uuid).first()
    if not org:
        raise HTTPException(404, f"Organization {org_id} not found")

    if body.accent_color is not None and not HEX_COLOR_RE.match(body.accent_color):
        raise HTTPException(400, "accent_color must be a hex color like '#7BE33F'")

    branding = db.query(Branding).filter_by(org_id=org_uuid).first()
    if branding is None:
        branding = Branding(org_id=org_uuid)
        db.add(branding)

    for field in ("display_name", "logo_url", "accent_color", "support_email", "custom_domain"):
        value = getattr(body, field)
        if value is not None:
            setattr(branding, field, value)
    branding.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(branding)
    return _branding_dict(branding)


@app.get("/api/organizations/{org_id}/branding")
async def get_branding(org_id: str, db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    """Get an organization's white-label settings, or null if none are set.
    Requires membership in that organization."""
    try:
        org_uuid = UUID(org_id)
    except ValueError:
        raise HTTPException(400, "Invalid org_id format")

    require_membership(db, current_user, org_uuid)

    branding = db.query(Branding).filter_by(org_id=org_uuid).first()
    return _branding_dict(branding)


class ApiKeyCreateRequest(BaseModel):
    """Request to create an API key."""
    org_id: str
    name: str


@app.post("/api/keys")
@limiter.limit("10/minute")
async def create_key(request: Request, body: ApiKeyCreateRequest, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    """
    Create a new API key for an organization. Requires membership in that
    organization — this used to be the whole hole: anyone could mint a key
    for any org_id, no proof of ownership required at all.

    Returns the plaintext key ONCE — it is never shown or recoverable
    again after this response. Store it now; to rotate, revoke this one
    and create a new one.
    """
    try:
        org_uuid = UUID(body.org_id)
    except ValueError:
        raise HTTPException(400, "Invalid org_id format")

    require_membership(db, current_user, org_uuid)

    if not db.query(Organization).filter_by(id=org_uuid).first():
        raise HTTPException(404, f"Organization {body.org_id} not found")
    if not body.name.strip():
        raise HTTPException(400, "name is required")

    result = create_api_key(db, org_uuid, body.name.strip())
    return result.dict()


@app.get("/api/keys")
async def get_keys(org_id: str, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    """
    List an organization's API keys — never the plaintext or the hash,
    only enough to tell them apart (name, prefix, last used, revoked).
    Requires membership in that organization.
    """
    try:
        org_uuid = UUID(org_id)
    except ValueError:
        raise HTTPException(400, "Invalid org_id format")

    require_membership(db, current_user, org_uuid)

    keys = list_api_keys(db, org_uuid)
    return {"total": len(keys), "keys": [k.dict() for k in keys]}


@app.delete("/api/keys/{key_id}")
async def delete_key(key_id: str, org_id: str, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    """Revoke an API key. Soft delete — the row stays, revoked_at is set.
    Requires membership in that organization."""
    try:
        key_uuid = UUID(key_id)
        org_uuid = UUID(org_id)
    except ValueError:
        raise HTTPException(400, "Invalid id format")

    require_membership(db, current_user, org_uuid)

    if not revoke_api_key(db, key_uuid, org_uuid):
        raise HTTPException(404, "API key not found for this organization")
    return {"revoked": True}


@app.get("/api/scans")
async def list_scans(db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    """List scans belonging to organizations the caller is a member of,
    most recent first. (Used to return every scan in the system to anyone —
    including the confidential `evidence` a scan captured.)"""
    org_ids = [m.org_id for m in db.query(Membership).filter_by(user_id=current_user.id).all()]
    if not org_ids:
        return {"total": 0, "scans": []}

    scans = (
        db.query(DBScan)
        .filter(DBScan.org_id.in_(org_ids))
        .order_by(DBScan.created_at.desc())
        .limit(100)
        .all()
    )
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
async def get_scan(scan_id: str, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    """Get a specific scan with all its results. 404s (not 403) for a scan
    that exists but belongs to an org the caller isn't a member of — so
    probing scan ids can't distinguish "not yours" from "doesn't exist"."""
    try:
        scan_uuid = UUID(scan_id)
    except ValueError:
        raise HTTPException(400, "Invalid scan_id format")

    scan = db.query(DBScan).filter_by(id=scan_uuid).first()
    if not scan:
        raise HTTPException(404, f"Scan {scan_id} not found")

    if not db.query(Membership).filter_by(user_id=current_user.id, org_id=scan.org_id).first():
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
@limiter.limit("5/minute")
async def scan(request: Request, body: ScanRequest, db: Session = Depends(get_db),
                api_key_org: UUID | None = Depends(resolve_org_from_api_key),
                current_user: User | None = Depends(get_current_user_optional)):
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
        Otherwise body.org_id is honoured only for a logged-in caller who
        is a member of that org (this used to accept any org_id from
        anyone — the same hole as the old /api/keys). A mode="prompt" call
        with neither stays fully anonymous and unauthenticated on purpose:
        that's the free, no-signup demo path, and it never touches a live
        third-party system, so there is nothing to protect.

    RATE LIMIT
        5/minute per IP — each call makes ~21 real Mistral API calls, so
        unrestricted access here is unrestricted cost, not just a DoS risk.
    """
    if body.mode == "prompt" and not body.system_prompt.strip():
        raise HTTPException(400, "system_prompt is required in prompt mode")
    if body.mode == "api" and not body.api_url.strip():
        raise HTTPException(400, "api_url is required in api mode")

    effective_org_id: UUID | None = api_key_org
    if effective_org_id is None and body.org_id:
        try:
            effective_org_id = UUID(body.org_id)
        except ValueError:
            raise HTTPException(400, "Invalid org_id format")
        # org_id came from the request body, not a verified API key — the
        # caller must prove they belong to that org before we act as it.
        if current_user is None:
            raise HTTPException(
                401,
                "Log in (Authorization: Bearer <token>) to run a scan as this "
                "organization, or omit org_id, or use a valid X-API-Key."
            )
        require_membership(db, current_user, effective_org_id)

    # PLAYBOOK §5: active attacks (mode="api") against a real endpoint
    # require verified ownership of that domain. mode="prompt" is exempt —
    # it only replays text the caller submitted themselves, never a live
    # third-party system.
    if body.mode == "api":
        if effective_org_id is None:
            raise HTTPException(
                403,
                "An org_id (or a valid X-API-Key) is required for mode='api'. "
                "Verify ownership of the target domain first via "
                "/api/ownership/challenge and /api/ownership/verify."
            )

        domain = urlparse(body.api_url).netloc or body.api_url
        if not is_domain_verified(db, effective_org_id, domain):
            raise HTTPException(
                403,
                f"Ownership of '{domain}' is not verified for this organization. "
                f"Active attacks are blocked until verification completes "
                f"(POST /api/ownership/challenge, then /api/ownership/verify)."
            )

    # If the caller did not tell us the secret, try to find it ourselves.
    # Without a canary, layer 1 of the judge cannot run at all.
    canary = body.canary or detect_canary(body.system_prompt)

    target = Target(
        mode=body.mode,
        system_prompt=body.system_prompt,
        api_url=body.api_url,
        api_headers=body.api_headers,
        canary=canary,
    )

    # The scan pushes results into this queue; the response reads from it.
    queue: asyncio.Queue = asyncio.Queue()
    report_holder = {}  # Temporary storage for the report

    async def on_result(result, done, total):
        await queue.put({"type": "result", "done": done, "total": total, "result": result})

    async def worker():
        try:
            report = await run_scan(target, body.categories, on_result)
            report_holder["report"] = report
            await queue.put({"type": "complete", "report": report})
        except Exception as e:
            await queue.put({"type": "error", "message": str(e)})
        finally:
            await queue.put(None)  # sentinel: nothing more is coming

    async def stream():
        library = load_library()
        selected = library.attacks
        if body.categories:
            selected = [a for a in selected if a.category in body.categories]
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
                    await _save_scan_to_db(db, body, report, report.get("duration_s", 0), effective_org_id)
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
