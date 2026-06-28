from __future__ import annotations

import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from models import PageContent


PRICE_PATTERNS = [
    r"\$\s?([\d,]{5,12})",
    r"MXN\s?([\d,]{5,12})",
    r"([\d,]{5,12})\s?pesos",
]


def extract_price(text: str) -> int | None:
    for pattern in PRICE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw = match.group(1).replace(",", "")
            try:
                return int(raw)
            except ValueError:
                return None
    return None


def extract_property_links(page: PageContent) -> list[str]:
    if not page.text:
        return []

    soup = BeautifulSoup(page.text, "html.parser")
    links = []

    for a in soup.select("a[href]"):
        href = a.get("href")
        text = a.get_text(" ", strip=True).lower()

        if not href:
            continue

        looks_like_property = any(
            word in text or word in href.lower()
            for word in [
                "remate",
                "casa",
                "departamento",
                "propiedad",
                "inmueble",
                "venta",
            ]
        )

        if looks_like_property:
            links.append(href)

    return list(set(links))