from __future__ import annotations

from models import SearchCriteria


def build_queries(criteria: SearchCriteria) -> list[str]:
    queries: list[str] = []

    for colonia in criteria.colonias:
        queries.extend(
            [
                f'"{colonia}" "remate bancario" casa CDMX',
                f'"{colonia}" "casa en remate" CDMX',
                f'"{colonia}" "adjudicado" "casa" CDMX',
                f'"{colonia}" "listo para escriturar" casa CDMX',
                f'site:propiedades.com "{colonia}" "casas remates"',
                f'site:inmuebles24.com "{colonia}" "remate"',
                f'site:lamudi.com.mx "{colonia}" "remate"',
                f'site:mercadolibre.com.mx "{colonia}" "remate bancario"',
                f'site:vivanuncios.com.mx "{colonia}" "remate bancario"',
            ]
        )

    return queries