"""Same-origin redirect helpers that reject untrusted destinations."""

from urllib.parse import urljoin, urlsplit

from flask import redirect, request, url_for


def is_safe_redirect_target(target, host_url=None):
    if not target or not isinstance(target, str):
        return False
    if "\\" in target or any(ord(character) < 32 for character in target):
        return False

    trusted_base = urlsplit(host_url or request.host_url)
    candidate = urlsplit(urljoin(trusted_base.geturl(), target))
    return (
        candidate.scheme in {"http", "https"}
        and candidate.scheme == trusted_base.scheme
        and candidate.netloc == trusted_base.netloc
    )


def safe_local_path(target, fallback=None):
    """Return a same-origin path suitable for storing in a signed session."""

    if not is_safe_redirect_target(target):
        return fallback
    parsed = urlsplit(urljoin(request.host_url, target))
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    if parsed.fragment:
        path = f"{path}#{parsed.fragment}"
    return path


def redirect_to_safe_target(target, fallback_endpoint, **fallback_values):
    safe_target = safe_local_path(target)
    return redirect(safe_target or url_for(fallback_endpoint, **fallback_values))
