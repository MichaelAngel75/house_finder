from __future__ import annotations

import re
from models import SearchResult


PRICE_PATTERNS = [
    r"\$\s?([\d,]{5,12})",
    r"MXN\s?([\d,]{5,12})",
    r"([\d,]{5,12})\s?pesos",
]


BEDROOM_PATTERNS = [
    r"(\d+)\s*rec[aá]mara",
    r"(\d+)\s*recamaras",
    r"(\d+)\s*habitación",
    r"(\d+)\s*habitaciones",
]


BATHROOM_PATTERNS = [
    r"(\d+)\s*bañ",
    r"(\d+)\s*bath",
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


def extract_bedrooms(text: str) -> int | None:
    for pattern in BEDROOM_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return int(match.group(1))

    return None


def extract_bathrooms(text: str) -> int | None:
    for pattern in BATHROOM_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return int(match.group(1))

    return None


def enrich_search_result(result: SearchResult) -> SearchResult:
    text = f"{result.title} {result.snippet}"

    return result.model_copy(
        update={
            "price": result.price or extract_price(text),
            "bedrooms": result.bedrooms or extract_bedrooms(text),
            "bathrooms": result.bathrooms or extract_bathrooms(text),
        }
    )