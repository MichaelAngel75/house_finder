from __future__ import annotations

import json
from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL
from models import SearchCriteria, SearchResult, PageContent, Classification
from app_logger import get_logger, log_input, log_output

logger = get_logger(__name__)


LOW_RISK_TERMS = [
    "escriturado",
    "listo para escriturar",
    "adjudicado",
    "posesión",
    "posesion",
]

HIGH_RISK_TERMS = [
    "cesión de derechos litigiosos",
    "cesion de derechos litigiosos",
    "derechos litigiosos",
    "juicio en proceso",
    "ocupado",
    "sin posesión",
    "sin posesion",
    "no se puede visitar",
    "no visitable",
]


def page_to_text(page: PageContent | None) -> str:
    if page is None:
        return ""

    for attr in ("html", "content", "text", "body", "raw_html"):
        value = getattr(page, attr, None)
        if value:
            return str(value)

    if hasattr(page, "model_dump"):
        data = page.model_dump()
        for key in ("html", "content", "text", "body", "raw_html"):
            value = data.get(key)
            if value:
                return str(value)

    return ""


def _clean_int(value) -> int | None:
    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    if isinstance(value, str):
        cleaned = (
            value.replace("$", "")
            .replace(",", "")
            .replace("MXN", "")
            .replace("mxn", "")
            .replace("pesos", "")
            .strip()
        )

        if cleaned.isdigit():
            return int(cleaned)

    return None


def _base_classification_fields(result: SearchResult) -> dict:
    return {
        "criteria_id": result.criteria_id,
        "query": result.query,
        "title": result.title,
        "snippet": result.snippet,
        "url": result.url,
        "source_domain": result.source_domain,
    }


def _criteria_matches(
    *,
    price: int | None,
    location: str | None,
    bedrooms: int | None,
    bathrooms: int | None,
    criteria: SearchCriteria,
) -> dict:
    matches_price_range = (
        price is not None
        and criteria.rango_min <= price <= criteria.rango_max
    )

    matches_bedrooms = (
        criteria.recamaras is None
        or bedrooms is None
        or bedrooms >= criteria.recamaras
    )

    matches_bathrooms = (
        criteria.banios is None
        or bathrooms is None
        or bathrooms >= criteria.banios
    )

    matches_location = True

    if location:
        location_lower = location.lower()
        matches_location = (
            any(colonia.lower() in location_lower for colonia in criteria.colonias)
            or criteria.state.lower() in location_lower
        )

    return {
        "matches_price_range": matches_price_range,
        "matches_bedrooms": matches_bedrooms,
        "matches_bathrooms": matches_bathrooms,
        "matches_location": matches_location,
    }


def _apply_final_include(
    *,
    llm_include: bool,
    risk_level: str,
    matches: dict,
) -> bool:
    return (
        llm_include
        and risk_level in {"very_low", "low"}
        and matches["matches_price_range"]
        and matches["matches_bedrooms"]
        and matches["matches_bathrooms"]
        and matches["matches_location"]
    )


def heuristic_classify(
    result: SearchResult,
    criteria: SearchCriteria,
    page: PageContent | None = None,
) -> Classification:
    page_text = page_to_text(page)
    text = f"{result.title} {result.snippet} {page_text}".lower()

    is_remate = any(
        term in text
        for term in ["remate", "adjudicado", "adjudicación", "adjudicacion"]
    )

    red_flags = [term for term in HIGH_RISK_TERMS if term in text]
    low_flags = [term for term in LOW_RISK_TERMS if term in text]

    price = result.price
    location = result.location
    bedrooms = result.bedrooms
    bathrooms = result.bathrooms

    matches = _criteria_matches(
        price=price,
        location=location,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        criteria=criteria,
    )

    if red_flags:
        return Classification(
            **_base_classification_fields(result),
            price=price,
            price_source=result.price_source or "not_found",
            location=location,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            is_remate=is_remate,
            remate_stage="unknown",
            risk_level="high",
            include=False,
            confidence=0.75,
            reason=f"Excluded by high-risk terms: {', '.join(red_flags)}",
            red_flags=red_flags,
            **matches,
        )

    llm_like_include = bool(is_remate and low_flags)

    final_include = _apply_final_include(
        llm_include=llm_like_include,
        risk_level="low" if llm_like_include else "unknown",
        matches=matches,
    )

    return Classification(
        **_base_classification_fields(result),
        price=price,
        price_source=result.price_source or "not_found",
        location=location,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        is_remate=is_remate,
        remate_stage="possible_low_risk" if llm_like_include else "unknown",
        risk_level="low" if llm_like_include else "unknown",
        include=final_include,
        confidence=0.65 if llm_like_include else 0.45,
        reason=(
            "Candidate remate with lower-risk indicators."
            if llm_like_include
            else "Not enough evidence for low-risk remate."
        ),
        red_flags=[],
        **matches,
    )


def llm_classify(
    result: SearchResult,
    criteria: SearchCriteria,
    page: PageContent | None = None,
) -> Classification:
    if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key_here":
        return heuristic_classify(result, criteria, page)

    client = OpenAI(api_key=OPENAI_API_KEY)

    page_text = page_to_text(page)[:8000]

    prompt = f"""
You classify Mexican real estate listings for remate risk.

Important:
You can only use the information provided below. Do not invent facts.
If price, location, bedrooms, or bathrooms are not clearly present, return null for those fields.

Goal:
Extract property facts and classify remate legal risk.

The user's search criteria are hard filters:
- Operation: {criteria.operacion}
- Minimum price MXN: {criteria.rango_min}
- Maximum price MXN: {criteria.rango_max}
- Required bedrooms: {criteria.recamaras}
- Required bathrooms: {criteria.banios}
- Target neighborhoods: {", ".join(criteria.colonias)}
- Target state/region: {criteria.state}

Risk include guidance:
Only include listings that appear to be VERY LOW or LOW risk.

Low-risk indicators:
- escriturado
- listo para escriturar
- adjudicado
- adjudicado with clear possession
- clear legal stage
- possession appears clear

Exclude when:
- cesion de derechos litigiosos
- derechos litigiosos
- juicio en proceso
- inmueble ocupado
- sin posesion
- no se puede visitar
- legal stage unclear
- cash-only with unclear legal status
- not enough evidence

Extract these property fields if explicitly available:
- price in MXN as integer, example 950000
- location / neighborhood
- bedrooms as integer
- bathrooms as integer

Return ONLY valid JSON with this schema:
{{
  "price": 950000,
  "price_source": "title|snippet|page_text|not_found",
  "location": "string or null",
  "bedrooms": 2,
  "bathrooms": 1,
  "is_remate": true,
  "remate_stage": "string or unknown",
  "risk_level": "very_low|low|medium|high|unknown",
  "include": true,
  "confidence": 0.0,
  "reason": "brief explanation",
  "red_flags": ["string"]
}}

Price extraction rules:
- Extract price only when explicitly shown in the provided text.
- Return price as integer MXN only.
- If the text says "$950,000", return 950000.
- If the text says "$1.7 MDP", return 1700000.
- If there are several prices because the URL is a listing/search page, return null and set price_source="not_found".
- Do not infer or estimate price.

Search result:
Title: {result.title}
Snippet: {result.snippet}
URL: {result.url}
Domain: {result.source_domain}
Query: {result.query}

Current extracted fields:
Price: {result.price}
Location: {result.location}
Bedrooms: {result.bedrooms}
Bathrooms: {result.bathrooms}

Fetched page text:
{page_text}
"""

    log_input(logger, "openai prompt", prompt)

    response = client.responses.create(
        model=OPENAI_MODEL,
        input=prompt,
        temperature=0,
    )

    raw = response.output_text.strip()
    log_output(logger, "openai raw response", raw)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        fallback = heuristic_classify(result, criteria, page)
        fallback.reason = "LLM did not return valid JSON. Used heuristic fallback."
        return fallback

    llm_price = _clean_int(data.get("price"))
    final_price = result.price or llm_price

    if result.price:
        final_price_source = result.price_source or "parser"
    elif llm_price:
        final_price_source = data.get("price_source") or "llm"
    else:
        final_price_source = "not_found"

    final_location = data.get("location") or result.location
    final_bedrooms = _clean_int(data.get("bedrooms")) or result.bedrooms
    final_bathrooms = _clean_int(data.get("bathrooms")) or result.bathrooms

    risk_level = data.get("risk_level") or "unknown"
    llm_include = bool(data.get("include", False))

    matches = _criteria_matches(
        price=final_price,
        location=final_location,
        bedrooms=final_bedrooms,
        bathrooms=final_bathrooms,
        criteria=criteria,
    )

    final_include = _apply_final_include(
        llm_include=llm_include,
        risk_level=risk_level,
        matches=matches,
    )

    reason = data.get("reason", "")

    if llm_include and not final_include:
        failed_filters = [
            name
            for name, passed in matches.items()
            if not passed
        ]

        reason = (
            f"{reason} Excluded by deterministic filters: "
            f"{', '.join(failed_filters)}."
        ).strip()

    return Classification(
        **_base_classification_fields(result),
        price=final_price,
        price_source=final_price_source,
        location=final_location,
        bedrooms=final_bedrooms,
        bathrooms=final_bathrooms,
        is_remate=bool(data.get("is_remate", False)),
        remate_stage=data.get("remate_stage") or "unknown",
        risk_level=risk_level,
        include=final_include,
        confidence=float(data.get("confidence", 0.0)),
        reason=reason,
        red_flags=data.get("red_flags", []) or [],
        **matches,
    )