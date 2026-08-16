"""
User authentication: register, log in, and prove who is calling.

WHY THIS EXISTS
    Every org-scoped endpoint (organizations, API keys, branding, ownership
    verification) used to trust whatever org_id a caller sent — no login,
    no proof of identity. Anyone could mint an API key for any organization
    just by knowing its id. This file is what closes that gap.

WHAT STAYS ANONYMOUS ON PURPOSE
    POST /api/scan with mode="prompt" and no org_id and no X-API-Key still
    works with no login at all — that is the free, no-signup demo path the
    whole course pitch depends on, and it never touches a live third-party
    system, so there is nothing here to protect. Login only matters once a
    caller wants to act *as* an organization.

DESIGN
    - Passwords: bcrypt (via the `bcrypt` package directly — no need for
      passlib's extra abstraction for one algorithm).
    - Sessions: a JWT bearer token in the Authorization header, not a
      cookie. The frontend is a set of static, fetch()-based pages already;
      a bearer token is the simpler fit and sidesteps CSRF entirely (unlike
      cookies, it's never sent automatically by the browser).
    - Authorization: `Membership` (already in models.py, unused until now)
      is the source of truth for "can this user act on this org". Any role
      (owner/admin/member) can do anything for now — splitting permissions
      by role is a fast follow, not a blocker.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from . import config
from .database import get_db
from .models import User, Membership


# --------------------------------------------------------------------- passwords

def hash_password(plaintext: str) -> str:
    return bcrypt.hashpw(plaintext.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plaintext: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plaintext.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Malformed hash — never crash the login endpoint over it.
        return False


# A fixed hash with no matching plaintext, computed once at import time.
# WHY: if a login checks `user and verify_password(...)`, a nonexistent
# email short-circuits before bcrypt ever runs, returning in a few ms —
# while a real account with the wrong password takes bcrypt's ~150-200ms.
# That timing gap alone lets an attacker enumerate registered emails, even
# though the error message is identical either way. Callers should run
# verify_password(password, user.password_hash if user else DUMMY_HASH)
# unconditionally, so both paths cost the same.
DUMMY_HASH = hash_password("no-account-has-this-password")


# --------------------------------------------------------------------------- JWT

def create_access_token(user_id: UUID, token_version: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "tv": token_version,
        "iat": now,
        "exp": now + timedelta(hours=config.JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def decode_access_token(token: str) -> tuple[UUID, int]:
    """Raises jwt.PyJWTError (caught by the caller) if invalid or expired."""
    payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
    return UUID(payload["sub"]), int(payload.get("tv", 0))


# --------------------------------------------------------------- FastAPI wiring

async def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """
    Required auth — raises 401 if there is no valid token. Use this on any
    endpoint that must have a logged-in caller (registering an org, issuing
    a key, reading someone's scan history).
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or malformed Authorization header. Expected: Bearer <token>")

    token = authorization[len("Bearer "):]
    try:
        user_id, token_version = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired, log in again")
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")

    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(401, "User no longer exists")
    if token_version != user.token_version:
        # Either this user logged out (token_version bumped) or every
        # session was force-revoked — either way, this token predates that.
        raise HTTPException(401, "Token revoked, log in again")
    return user


async def get_current_user_optional(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Optional auth — returns None instead of raising when there is no token.
    Use this on endpoints that stay usable anonymously (POST /api/scan) but
    should recognize a logged-in caller when one is present.
    """
    if not authorization:
        return None
    try:
        return await get_current_user(authorization, db)
    except HTTPException:
        return None


# Higher number = more privilege. "member" is the floor every role clears.
ROLE_RANK = {"member": 0, "admin": 1, "owner": 2}


def require_membership(db: Session, user: User, org_id: UUID, min_role: str = "member") -> Membership:
    """
    Raises 403 if `user` has no Membership row for `org_id`, or if their role
    ranks below `min_role`. Call this at the top of every org-scoped endpoint,
    right after resolving org_id.

    Default is "member" — any role clears it, so existing calls are unaffected.
    Pass min_role="admin" for actions with organization-wide impact (revoking
    a key someone else depends on, changing branding, verifying domain
    ownership) that a plain member should not be able to do alone.
    """
    membership = db.query(Membership).filter_by(user_id=user.id, org_id=org_id).first()
    if not membership:
        raise HTTPException(403, "You are not a member of this organization")

    if ROLE_RANK.get(membership.role, -1) < ROLE_RANK.get(min_role, 999):
        raise HTTPException(
            403,
            f"This action requires the '{min_role}' role or higher "
            f"(you are '{membership.role}')"
        )
    return membership
