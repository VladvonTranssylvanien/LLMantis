"""
Ownership verification via DNS TXT record.

User flow:
    1. POST /api/ownership/challenge
       Request: {"org_id": "...", "domain": "example.com"}
       Response: {"token": "llmantis-verify-abc123", "instructions": "Add this TXT record..."}

    2. User adds DNS TXT record:
       _llmantis.example.com TXT llmantis-verify-abc123

    3. POST /api/ownership/verify
       Request: {"org_id": "...", "domain": "example.com", "token": "llmantis-verify-abc123"}
       Response: {"verified": true, "verified_at": "2026-08-16T..."}

Why DNS TXT?
    - No setup required (user already controls DNS)
    - Standard practice (ACME for Let's Encrypt, etc.)
    - Hard to fake (requires actual DNS access)

Security:
    - Token is 24 random characters (cryptographically secure)
    - Challenge expires after 24 hours if not verified
    - Verification record is what gates active attacks in /api/scan (mode="api")
"""

import secrets
import dns.resolver
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from .models import OwnershipVerification

CHALLENGE_TTL_HOURS = 24
VERIFICATION_TTL_DAYS = 90  # re-verify every 90 days, per implementation plan


class OwnershipResult(BaseModel):
    """Result of an ownership operation."""
    domain: str
    verified: bool
    token: Optional[str] = None
    verified_at: Optional[str] = None
    error: Optional[str] = None
    instructions: Optional[str] = None


def _normalize_domain(domain: str) -> str:
    domain = domain.lower().strip()
    if domain.startswith("http://") or domain.startswith("https://"):
        domain = domain.split("://")[1].split("/")[0]
    return domain.rstrip("/")


def generate_token() -> str:
    """Generate a cryptographically secure verification token."""
    return f"llmantis-verify-{secrets.token_hex(12)}"


async def create_challenge(db: Session, org_id: UUID, domain: str) -> OwnershipResult:
    """
    Create a DNS verification challenge and persist it as 'pending'.

    A new challenge replaces any prior pending challenge for the same
    org+domain (old tokens for that pair stop being valid).
    """
    domain = _normalize_domain(domain)
    token = generate_token()
    now = datetime.utcnow()

    # Invalidate previous pending challenges for this org+domain
    db.query(OwnershipVerification).filter_by(
        org_id=org_id, domain=domain, status="pending"
    ).delete()

    record = OwnershipVerification(
        id=uuid4(),
        org_id=org_id,
        domain=domain,
        method="dns_txt",
        token=token,
        status="pending",
        expires_at=now + timedelta(hours=CHALLENGE_TTL_HOURS),
        created_at=now,
    )
    db.add(record)
    db.commit()

    instructions = f"""
Add this DNS TXT record to verify ownership of {domain}:

Record Name: _llmantis.{domain}
Record Type: TXT
Record Value: {token}

Steps (varies by registrar):
1. Log in to your DNS provider (GoDaddy, Namecheap, Route53, Cloudflare, etc.)
2. Find the DNS management section
3. Add a new TXT record with the name and value above
4. Save changes (may take 5-15 minutes to propagate)
5. Come back here and click "Verify" to confirm

This challenge expires in {CHALLENGE_TTL_HOURS} hours. After verification,
you can run active security tests (mode="api") against {domain}.
"""

    return OwnershipResult(
        domain=domain,
        verified=False,
        token=token,
        instructions=instructions.strip()
    )


async def verify_ownership(db: Session, org_id: UUID, domain: str, token: str) -> OwnershipResult:
    """
    Verify ownership by checking DNS TXT record against the pending challenge.

    On success, marks the record 'verified' with a 90-day expiry — that
    row is what /api/scan checks before allowing an active (mode="api") scan.
    """
    domain = _normalize_domain(domain)

    record = db.query(OwnershipVerification).filter_by(
        org_id=org_id, domain=domain, token=token, status="pending"
    ).first()

    if not record:
        return OwnershipResult(
            domain=domain,
            verified=False,
            error="No pending challenge found for this org/domain/token combination. "
                  "Request a new challenge via /api/ownership/challenge."
        )

    if record.expires_at and record.expires_at < datetime.utcnow():
        db.delete(record)
        db.commit()
        return OwnershipResult(
            domain=domain,
            verified=False,
            error="Challenge expired. Request a new one via /api/ownership/challenge."
        )

    txt_record_name = f"_llmantis.{domain}"

    try:
        answers = dns.resolver.resolve(txt_record_name, "TXT")
        found = any(
            txt_string.decode("utf-8") == token
            for rdata in answers
            for txt_string in rdata.strings
        )
    except dns.resolver.NXDOMAIN:
        return OwnershipResult(
            domain=domain,
            verified=False,
            error=f"DNS record not found: {txt_record_name}. "
                  f"Please add the TXT record and wait 5-15 minutes for propagation."
        )
    except dns.resolver.NoAnswer:
        return OwnershipResult(
            domain=domain,
            verified=False,
            error=f"No TXT records found at {txt_record_name}. "
                  f"Please add the verification TXT record."
        )
    except Exception as e:
        return OwnershipResult(
            domain=domain,
            verified=False,
            error=f"DNS lookup failed: {str(e)}"
        )

    if not found:
        return OwnershipResult(
            domain=domain,
            verified=False,
            error=f"DNS TXT record found at {txt_record_name}, but token not found. "
                  f"Expected: {token}"
        )

    now = datetime.utcnow()
    record.status = "verified"
    record.verified_at = now
    record.expires_at = now + timedelta(days=VERIFICATION_TTL_DAYS)
    db.commit()

    return OwnershipResult(
        domain=domain,
        verified=True,
        verified_at=now.isoformat(),
        token=token
    )


def is_domain_verified(db: Session, org_id: UUID, domain: str) -> bool:
    """
    Gate check used by /api/scan before running an active (mode="api") scan.

    True only if there is a 'verified' record for this org+domain that has
    not expired (re-verification required every 90 days).
    """
    domain = _normalize_domain(domain)
    record = db.query(OwnershipVerification).filter_by(
        org_id=org_id, domain=domain, status="verified"
    ).order_by(OwnershipVerification.verified_at.desc()).first()

    if not record:
        return False
    if record.expires_at and record.expires_at < datetime.utcnow():
        return False
    return True
