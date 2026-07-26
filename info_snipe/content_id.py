import hashlib
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

_TRACKING_PREFIXES = ("utm_",)
_TRACKING_PARAMS = {"gclid", "fbclid", "ref", "ref_src", "cmp", "igshid"}


def canonicalize_url(url: str) -> str:
    """Normalize a URL so trivially different links to the same article collapse
    to the same string (scheme, www, trailing slash, tracking params)."""
    parsed = urlparse(url.strip())
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = parsed.path.rstrip("/") or "/"
    query_pairs = sorted(
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if not k.lower().startswith(_TRACKING_PREFIXES) and k.lower() not in _TRACKING_PARAMS
    )
    return urlunparse(("https", netloc, path, "", urlencode(query_pairs), ""))


def make_content_id(*, url, title: str, source_name: str) -> str:
    """Stable id for an article, used to detect and skip already-seen content.

    Prefers the canonicalized URL as the identity basis; falls back to
    source+title for the rare item with no URL.
    """
    if url:
        basis = canonicalize_url(url)
    else:
        basis = f"{source_name.strip().lower()}:{title.strip().lower()}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:24]
