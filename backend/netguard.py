"""
Where a server-side request is allowed to go.

Two places in this codebase take a URL from a caller and fetch it from our
server: the Art.-50 check (backend/art50engine.py, which drives a browser and
re-checks every request the page makes, not just the first) and the active
api-mode scan (backend/scanner.py). Both are SSRF surfaces — without a
check, a caller can point us at http://localhost:5432, at
http://169.254.169.254/ (the cloud metadata endpoint on AWS/GCP/Azure), or
at anything else on our own private network, and use our server as a proxy
to reach it.

The rule is the same for both, so it lives here once rather than being
copy-pasted and then drifting.
"""

import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeUrlError(Exception):
    """Raised when a URL resolves to a private/internal address."""


def is_private_url(url: str) -> bool:
    """
    True if this URL resolves to a non-public address. Unlike
    assert_public_host it never raises for an unresolvable host — an
    unknown host is treated as not-private, and the caller's own
    fetch will fail on it later with a clearer error.

    Used to decide *policy* (may this target be scanned at all), where
    assert_public_host enforces it.
    """
    try:
        assert_public_host(url)
        return False
    except UnsafeUrlError:
        return True


def assert_public_host(url: str) -> None:
    """
    Refuse anything that resolves to a private, loopback, link-local or
    otherwise non-public address. Raises UnsafeUrlError.

    Checks every address the hostname resolves to, not just the first —
    a name with both a public and a private A record must not slip
    through on ordering.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UnsafeUrlError(f"Unsupported scheme: {parsed.scheme!r}")
    if not parsed.hostname:
        raise UnsafeUrlError("URL has no hostname")

    try:
        addrs = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror as e:
        raise UnsafeUrlError(f"Could not resolve host: {e}") from e

    for _family, _, _, _, sockaddr in addrs:
        ip = ipaddress.ip_address(sockaddr[0])
        if (
            ip.is_private or ip.is_loopback or ip.is_link_local
            or ip.is_multicast or ip.is_reserved or ip.is_unspecified
        ):
            raise UnsafeUrlError(
                f"Refusing to fetch {parsed.hostname!r} — resolves to "
                f"non-public address {ip}"
            )
