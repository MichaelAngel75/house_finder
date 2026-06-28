from __future__ import annotations

from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode


DROP_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "n_src",
    "n_pg",
    "n_pos",
    "source",
    "ref",
}


def normalize_url(url: str) -> str:
    parsed = urlparse(url)

    kept_params = []

    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if key.lower() not in DROP_PARAMS:
            kept_params.append((key, value))

    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path.rstrip("/"),
            "",
            urlencode(kept_params),
            "",
        )
    )