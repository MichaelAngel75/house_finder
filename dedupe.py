from __future__ import annotations

from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

DROP_QUERY_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
}


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())

    scheme = parsed.scheme or "https"
    netloc = parsed.netloc.lower().replace("www.", "")

    query_pairs = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in DROP_QUERY_PARAMS
    ]

    normalized_query = urlencode(query_pairs)
    path = parsed.path.rstrip("/")

    return urlunparse((scheme, netloc, path, "", normalized_query, ""))


def domain_from_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower().replace("www.", "")