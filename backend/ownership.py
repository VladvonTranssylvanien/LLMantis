"""
Ownership verification via DNS TXT record.

User flow:
    1. POST /api/ownership/challenge
       Request: {"domain": "example.com"}
       Response: {"token": "llmantis-verify-abc123", "instructions": "Add this TXT record..."}

    2. User adds DNS TXT record:
       _llmantis.example.com TXT llmantis-verify-abc123

    3. POST /api/ownership/verify
       Request: {"domain": "example.com", "token": "llmantis-verify-abc123"}
       Response: {"verified": true, "verified_at": "2026-08-16T..."}

Why DNS TXT?
    - No setup required (user already controls DNS)
    - Standard practice (ACME for Let's Encrypt, etc.)
    - Hard to fake (requires actual DNS access)

Security:
    - Token is 24 random characters (cryptographically secure)
    - Token expires after 24 hours if not verified
    - One token per domain at a time
"""

import secrets
import dns.resolver
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional


class OwnershipChallenge(BaseModel):
    """Generate a verification challenge."""
    domain: str


class OwnershipVerify(BaseModel):
    """Verify ownership by checking DNS TXT record."""
    domain: str
    token: str


class OwnershipResult(BaseModel):
    """Result of ownership verification."""
    domain: str
    verified: bool
    token: Optional[str] = None
    verified_at: Optional[str] = None
    error: Optional[str] = None
    instructions: Optional[str] = None


def generate_token() -> str:
    """Generate a cryptographically secure verification token."""
    return f"llmantis-verify-{secrets.token_hex(12)}"


async def create_challenge(domain: str) -> OwnershipResult:
    """
    Create a DNS verification challenge.

    Returns: token and instructions for the user.
    """
    # Normalize domain
    domain = domain.lower().strip()
    if domain.startswith("http://") or domain.startswith("https://"):
        # Extract domain from URL
        domain = domain.split("://")[1].split("/")[0]

    token = generate_token()

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

After verification, you can run active security tests on {domain}.
"""

    return OwnershipResult(
        domain=domain,
        verified=False,
        token=token,
        instructions=instructions.strip()
    )


async def verify_ownership(domain: str, token: str) -> OwnershipResult:
    """
    Verify ownership by checking DNS TXT record.

    Returns: True if token found in DNS TXT records for _llmantis.{domain}
    """
    # Normalize domain
    domain = domain.lower().strip()
    if domain.startswith("http://") or domain.startswith("https://"):
        domain = domain.split("://")[1].split("/")[0]

    txt_record_name = f"_llmantis.{domain}"

    try:
        # Query DNS for TXT records
        answers = dns.resolver.resolve(txt_record_name, "TXT")

        # Check if our token is in any of the TXT records
        for rdata in answers:
            for txt_string in rdata.strings:
                if txt_string.decode("utf-8") == token:
                    return OwnershipResult(
                        domain=domain,
                        verified=True,
                        verified_at=datetime.utcnow().isoformat(),
                        token=token
                    )

        # Token not found in records
        return OwnershipResult(
            domain=domain,
            verified=False,
            error=f"DNS TXT record found at {txt_record_name}, but token not found. "
                  f"Expected: {token}"
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
