from __future__ import annotations

import json
from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL
from models import SearchResult, PageContent, Classification

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


def heuristic_classify(
    result: SearchResult,
    page: PageContent | None = None,
) -> Classification:
    text = f"{result.title} {result.snippet} {page.text if page else ''}".lower()

    is_remate = any(
        term in text
        for term in ["remate", "adjudicado", "adjudicación", "adjudicacion"]
    )

    red_flags = [term for term in HIGH_RISK_TERMS if term in text]
    low_flags = [term for term in LOW_RISK_TERMS if term in text]

    if red_flags:
        return Classification(
            criteria_id=result.criteria_id,
            query=result.query,
            title=result.title,
            snippet=result.snippet,
            url=result.url,
            source_domain=result.source_domain,
            is_remate=is_remate,
            remate_stage="unknown",
            risk_level="high",
            include=False,
            confidence=0.75,
            reason=f"Excluded by high-risk terms: {', '.join(red_flags)}",
            red_flags=red_flags,
        )

    if is_remate and low_flags:
        return Classification(
            criteria_id=result.criteria_id,
            query=result.query,
            title=result.title,
            snippet=result.snippet,
            url=result.url,
            source_domain=result.source_domain,
            is_remate=True,
            remate_stage="possible_low_risk",
            risk_level="low",
            include=True,
            confidence=0.65,
            reason=(
                "Candidate remate with lower-risk indicators: "
                f"{', '.join(low_flags)}"
            ),
            red_flags=[],
        )

    return Classification(
        criteria_id=result.criteria_id,
        query=result.query,
        title=result.title,
        snippet=result.snippet,
        url=result.url,
        source_domain=result.source_domain,
        is_remate=is_remate,
        remate_stage="unknown",
        risk_level="unknown",
        include=False,
        confidence=0.45,
        reason="Not enough evidence for low-risk remate.",
        red_flags=[],
    )


def llm_classify(
    result: SearchResult,
    page: PageContent | None = None,
) -> Classification:
    if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key_here":
        return heuristic_classify(result, page)

    client = OpenAI(api_key=OPENAI_API_KEY)

    page_text = page.text[:6000] if page and page.text else ""

    prompt = f"""
You classify Mexican real estate listings for remate risk.

Goal:
Only include listings that appear to be VERY LOW or LOW risk.

Include only when:
- The listing appears to be a remate or adjudicated property.
- The legal stage appears clear.
- It says or strongly implies escriturado, listo para escriturar, adjudicado with clear possession, or similar.

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

Return ONLY valid JSON with this schema:
{{
  "is_remate": true,
  "remate_stage": "string or unknown",
  "risk_level": "very_low|low|medium|high|unknown",
  "include": true,
  "confidence": 0.0,
  "reason": "brief explanation",
  "red_flags": ["string"]
}}

Search result:
Title: {result.title}
Snippet: {result.snippet}
URL: {result.url}
Domain: {result.source_domain}
Query: {result.query}

Fetched page text:
{page_text}
"""

    response = client.responses.create(
        model=OPENAI_MODEL,
        input=prompt,
        temperature=0,
    )

    raw = response.output_text.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        fallback = heuristic_classify(result, page)
        fallback.reason = "LLM did not return valid JSON. Used heuristic fallback."
        return fallback

    return Classification(
        criteria_id=result.criteria_id,
        query=result.query,
        title=result.title,
        snippet=result.snippet,
        url=result.url,
        source_domain=result.source_domain,
        is_remate=bool(data.get("is_remate", False)),
        remate_stage=data.get("remate_stage") or "unknown",
        risk_level=data.get("risk_level") or "unknown",
        include=bool(data.get("include", False)),
        confidence=float(data.get("confidence", 0.0)),
        reason=data.get("reason", ""),
        red_flags=data.get("red_flags", []) or [],
    )