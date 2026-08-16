"""
API keys — let a customer call the API programmatically (CI/CD pipeline,
integration) instead of through the browser, and let us attribute that
usage to the right organization.

USAGE
    Caller sends the key on every request:
        X-API-Key: llm_live_AbCdEfGh...

    We store only sha256(key) — never the plaintext. The plaintext is
    shown to the caller exactly once, in the response to POST /api/keys,
    and is not recoverable after that (rotate = revoke + create new).

WHY THIS MATTERS
    Without this, every /api/scan call is anonymous or requires the
    caller to already know their own org_id and paste it into every
    request. A key resolves the organization for us, which is what lets
    a CI pipeline run "scan our bot after every deploy" without a human
    in the loop, and lets us cap usage per subscription plan later.
"""

import hashlib
import secrets
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional

from fastapi import Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database import get_db
from .models import ApiKey

KEY_PREFIX = "llm_live_"


def _hash_key(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


def generate_key() -> str:
    """A new plaintext key. Never stored — only its hash is."""
    return KEY_PREFIX + secrets.token_urlsafe(24)


class ApiKeyCreated(BaseModel):
    """Returned exactly once, at creation. The plaintext is not stored."""
    id: str
    name: str
    key: str
    key_prefix: str
    created_at: str


class ApiKeySummary(BaseModel):
    """What GET /api/keys returns — never the plaintext or the hash."""
    id: str
    name: str
    key_prefix: str
    created_at: str
    last_used_at: Optional[str] = None
    revoked: bool = False


def create_api_key(db: Session, org_id: UUID, name: str) -> ApiKeyCreated:
    plaintext = generate_key()
    row = ApiKey(
        id=uuid4(),
        org_id=org_id,
        name=name,
        key_hash=_hash_key(plaintext),
        key_prefix=plaintext[:16],
        created_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return ApiKeyCreated(
        id=str(row.id),
        name=row.name,
        key=plaintext,
        key_prefix=row.key_prefix,
        created_at=row.created_at.isoformat(),
    )


def list_api_keys(db: Session, org_id: UUID) -> list[ApiKeySummary]:
    rows = db.query(ApiKey).filter_by(org_id=org_id).order_by(ApiKey.created_at.desc()).all()
    return [
        ApiKeySummary(
            id=str(r.id),
            name=r.name,
            key_prefix=r.key_prefix,
            created_at=r.created_at.isoformat(),
            last_used_at=r.last_used_at.isoformat() if r.last_used_at else None,
            revoked=r.revoked_at is not None,
        )
        for r in rows
    ]


def revoke_api_key(db: Session, key_id: UUID, org_id: UUID) -> bool:
    """Soft-delete: sets revoked_at. Returns False if not found for this org."""
    row = db.query(ApiKey).filter_by(id=key_id, org_id=org_id).first()
    if not row:
        return False
    row.revoked_at = datetime.utcnow()
    db.commit()
    return True


async def resolve_org_from_api_key(
    x_api_key: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> Optional[UUID]:
    """
    FastAPI dependency. Returns the org_id for a valid X-API-Key header,
    None if no header was sent, or raises 401 if the key is invalid or
    revoked. A missing header is not an error — most endpoints stay
    usable without a key; this only identifies the caller when present.
    """
    if not x_api_key:
        return None

    row = db.query(ApiKey).filter_by(key_hash=_hash_key(x_api_key)).first()
    if not row or row.revoked_at is not None:
        raise HTTPException(401, "Invalid or revoked API key")

    row.last_used_at = datetime.utcnow()
    db.commit()
    return row.org_id
