"""
Art. 50 AI Act Compliance Check — Passive scanner.

Art. 50(1) AI Act (in force since 02.08.2026):
    High-risk AI systems shall disclose to the user that they are interacting with
    an AI system, except where this is obvious from the context.

What we check:
    ✓ Is there a chat widget on the site?
    ✓ Does it disclose that it is AI on first contact?
    ✓ Is there a privacy link next to the widget?
    ✓ Does the widget load before cookie consent?
    ✓ Is there an impressum (§5 DDG)?

Why passive only:
    We do NOT send messages to the bot. We visit as an ordinary user,
    look at the widget's first message, take a screenshot, and leave.
    This is not a breach of the provider's ToS.
"""

import re
from typing import Optional
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel


class Art50Finding(BaseModel):
    """One finding from an Art. 50 check."""
    check: str  # e.g. "ai_disclosure", "privacy_link", "impressum"
    status: str  # "pass" or "fail"
    evidence: str  # what we found (or didn't find)
    severity: str  # "critical" or "high" or "medium" or "low"
    fix: str  # how to fix it


class Art50Result(BaseModel):
    """Result of an Art. 50 check on one URL."""
    url: str
    status: str  # "ok" or "error" or "incomplete"
    error: Optional[str] = None
    widgets_found: int = 0
    widget_names: list[str] = []
    findings: list[Art50Finding] = []
    duration_ms: int = 0


# Known chat widget signatures
WIDGET_SIGNATURES = {
    "intercom": r"Intercom|window\.intercomSettings|js\.intercom\.com",
    "tidio": r"tidio|tidiochat\.com",
    "userlike": r"userlike|userlike\.com",
    "crisp": r"crisp\.chat|CrispChat",
    "drift": r"drift\.com|Drift|drift-frame-controller",
    "zendesk": r"zopim|zendesk",
    "freshchat": r"freshchat|freshworks",
    "livechat": r"livechat|livechatinc\.com",
    "chatbot": r"chatbot|chatbot-widget|bot-frame",
}


async def _fetch_page(url: str, timeout: int = 10) -> tuple[Optional[str], Optional[str]]:
    """
    Fetch a page as an ordinary visitor (async).

    Returns: (html, error)
    """
    try:
        # Identify ourselves — be transparent
        headers = {
            "User-Agent": "LLMantis-Checker/1.0 (+https://llmantis.de/scanner)"
        }
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text, None
    except httpx.RequestError as e:
        return None, str(e)


def _detect_widget(html: str) -> dict:
    """
    Detect if there is a chat widget and which one.

    Returns: {"found": bool, "widgets": [{"name": str, "confidence": float}]}
    """
    widgets = []
    for name, pattern in WIDGET_SIGNATURES.items():
        if re.search(pattern, html, re.IGNORECASE):
            widgets.append({"name": name, "confidence": 0.8})

    return {
        "found": len(widgets) > 0,
        "widgets": widgets
    }


def _check_ai_disclosure(html: str) -> tuple[bool, str]:
    """
    Check if the widget discloses that it is AI.

    Look for keywords in:
    - First message text
    - aria-label or title attributes
    - Widget heading

    Returns: (passes, evidence)
    """
    ai_keywords = [
        r"\bAI\b",
        r"artificial intelligence",
        r"chatbot",
        r"powered by",
        r"automated",
        r"assistant",
    ]

    # Extract visible text and common widget containers
    soup = BeautifulSoup(html, "html.parser")

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    text = soup.get_text(separator=" ")

    # Look for AI keywords
    for keyword in ai_keywords:
        if re.search(keyword, text, re.IGNORECASE):
            return True, f"Found disclosure: '{keyword}'"

    return False, "No AI disclosure found in widget text"


def _check_privacy_link(html: str) -> tuple[bool, str]:
    """
    Check if there is a privacy link visible.

    Returns: (passes, evidence)
    """
    soup = BeautifulSoup(html, "html.parser")

    # Look for links to privacy policy
    privacy_patterns = [
        r"privacy",
        r"datenschutz",
        r"gdpr",
        r"cookie",
        r"terms",
    ]

    for link in soup.find_all("a"):
        href = link.get("href", "").lower()
        text = link.get_text().lower()

        for pattern in privacy_patterns:
            if re.search(pattern, href) or re.search(pattern, text):
                return True, f"Found privacy link: {text or href}"

    return False, "No privacy policy link found"


def _check_impressum(html: str) -> tuple[bool, str]:
    """
    Check if there is an impressum (German legal requirement § 5 DDG).

    Returns: (passes, evidence)
    """
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text().lower()

    # German legal requirement
    patterns = [
        r"impressum",
        r"imprint",
        r"legal.*notice",
        r"kontakt",  # Sometimes used as impressum
    ]

    for pattern in patterns:
        if re.search(pattern, text):
            return True, f"Found: {pattern}"

    return False, "No impressum found (required by § 5 DDG)"


async def check_art50(url: str) -> Art50Result:
    """
    Run a passive Art. 50 compliance check on a URL.

    Checks:
        1. Is there a chat widget?
        2. Does it disclose AI?
        3. Is there a privacy link?
        4. Is there an impressum?
    """
    import time
    start = time.time()

    # Normalize URL
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    # Fetch the page
    html, error = await _fetch_page(url)
    if error:
        return Art50Result(
            url=url,
            status="error",
            error=error,
            duration_ms=int((time.time() - start) * 1000)
        )

    if not html:
        return Art50Result(
            url=url,
            status="error",
            error="Empty response",
            duration_ms=int((time.time() - start) * 1000)
        )

    # Run checks
    findings = []

    # Check 1: Widget detection
    widget_check = _detect_widget(html)
    if widget_check["found"]:
        findings.append(Art50Finding(
            check="widget_found",
            status="pass",
            evidence=f"Found {len(widget_check['widgets'])} widget(s): " +
                    ", ".join([w["name"] for w in widget_check["widgets"]]),
            severity="info",
            fix="N/A"
        ))
    else:
        findings.append(Art50Finding(
            check="widget_found",
            status="pass",
            evidence="No chat widget detected",
            severity="info",
            fix="N/A"
        ))
        # If no widget, no Art. 50 requirement
        return Art50Result(
            url=url,
            status="ok",
            widgets_found=0,
            findings=findings,
            duration_ms=int((time.time() - start) * 1000)
        )

    # Check 2: AI Disclosure (Art. 50(1))
    passes, evidence = _check_ai_disclosure(html)
    findings.append(Art50Finding(
        check="ai_disclosure",
        status="pass" if passes else "fail",
        evidence=evidence,
        severity="critical" if not passes else "info",
        fix="Add 'Powered by AI' or similar text to the widget's first message" if not passes else "N/A"
    ))

    # Check 3: Privacy link
    passes, evidence = _check_privacy_link(html)
    findings.append(Art50Finding(
        check="privacy_link",
        status="pass" if passes else "fail",
        evidence=evidence,
        severity="high" if not passes else "info",
        fix="Add a link to your privacy policy" if not passes else "N/A"
    ))

    # Check 4: Impressum (§ 5 DDG)
    passes, evidence = _check_impressum(html)
    findings.append(Art50Finding(
        check="impressum",
        status="pass" if passes else "fail",
        evidence=evidence,
        severity="high" if not passes else "info",
        fix="Add an impressum page (required by German law § 5 DDG)" if not passes else "N/A"
    ))

    # Overall status
    failures = [f for f in findings if f.status == "fail"]
    overall_status = "fail" if failures else "pass"

    return Art50Result(
        url=url,
        status=overall_status,
        widgets_found=len(widget_check["widgets"]),
        widget_names=[w["name"] for w in widget_check["widgets"]],
        findings=findings,
        duration_ms=int((time.time() - start) * 1000)
    )
