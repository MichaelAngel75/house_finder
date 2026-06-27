import json
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL
from models import Listing, ClassifiedListing

client = OpenAI(api_key=OPENAI_API_KEY)


def classify_listing(listing: Listing) -> ClassifiedListing:
    prompt = f"""
Clasifica este anuncio inmobiliario en México.

Objetivo:
Solo incluir remates de riesgo MUY BAJO o BAJO.

Criterios:
- Incluir si parece escriturado, listo para escriturar, adjudicado con posesión clara.
- Excluir si menciona cesión de derechos litigiosos, juicio en proceso, ocupado, sin posesión, no visitable, o riesgo legal alto.
- Si no hay suficiente evidencia, excluir.

Devuelve únicamente JSON válido.

Campos:
{{
  "is_remate": boolean,
  "remate_stage": string | null,
  "risk_level": "very_low" | "low" | "medium" | "high" | "unknown",
  "include": boolean,
  "reason": string
}}

Anuncio:
Portal: {listing.portal}
Título: {listing.title}
Precio: {listing.price}
Ubicación: {listing.location}
Recámaras: {listing.bedrooms}
Baños: {listing.bathrooms}
Descripción: {listing.description}
URL: {listing.url}
"""

    response = client.responses.create(
        model=OPENAI_MODEL,
        input=prompt,
        temperature=0
    )

    raw = response.output_text.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {
            "is_remate": False,
            "remate_stage": None,
            "risk_level": "unknown",
            "include": False,
            "reason": "LLM no devolvió JSON válido."
        }

    return ClassifiedListing(
        **listing.model_dump(),
        is_remate=data.get("is_remate", False),
        remate_stage=data.get("remate_stage"),
        risk_level=data.get("risk_level", "unknown"),
        include=data.get("include", False),
        reason=data.get("reason", "")
    )