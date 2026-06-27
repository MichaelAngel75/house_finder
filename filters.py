import re
from models import Listing, SearchCriteria

POSITIVE_REMASE_WORDS = [
    "remate",
    "remate bancario",
    "adjudicado",
    "escriturado",
    "listo para escriturar",
    "posesión",
]

HIGH_RISK_WORDS = [
    "cesión de derechos litigiosos",
    "derechos litigiosos",
    "sin posesión",
    "ocupado",
    "juicio en proceso",
    "no se puede visitar",
    "no crédito",
    "solo contado",
    "solo recursos propios",
]


def normalize(text: str | None) -> str:
    return (text or "").lower().strip()


def matches_criteria(listing: Listing, criteria: SearchCriteria) -> bool:
    text = normalize(f"{listing.title} {listing.location} {listing.description}")

    if listing.price:
        if listing.price < criteria.rango_min or listing.price > criteria.rango_max:
            return False

    if criteria.recamaras and listing.bedrooms:
        if listing.bedrooms < criteria.recamaras:
            return False

    if criteria.banios and listing.bathrooms:
        if listing.bathrooms < criteria.banios:
            return False

    if criteria.colonias:
        found_colonia = any(colonia.lower() in text for colonia in criteria.colonias)
        if not found_colonia:
            return False

    return True


def looks_like_remate_candidate(listing: Listing) -> bool:
    text = normalize(f"{listing.title} {listing.description}")
    return any(word in text for word in POSITIVE_REMASE_WORDS)


def has_high_risk_words(listing: Listing) -> bool:
    text = normalize(f"{listing.title} {listing.description}")
    return any(word in text for word in HIGH_RISK_WORDS)


def parse_price(text: str) -> int | None:
    if not text:
        return None

    cleaned = text.replace(",", "").replace("$", "")
    match = re.search(r"(\d{5,10})", cleaned)

    if not match:
        return None

    return int(match.group(1))