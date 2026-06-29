from __future__ import annotations

from models import SearchCriteria

def build_queries(criteria: SearchCriteria) -> list[str]:
    queries: list[str] = []
    region = criteria.state

    for colonia in criteria.colonias:
        queries.extend([
            # f'site:tiktok.com "{colonia}" remate bancario {region}',
            # f'site:instagram.com "{colonia}" remate bancario {region}',
            # f'site:facebook.com "{colonia}" remate bancario {region}',
            # -----
            # f'site:propiedades.com "{colonia}" remate "{region}"',
            # f'site:inmuebles24.com "{colonia}" remate "{region}"',
            # f'site:lamudi.com.mx "{colonia}" remate "{region}"',
            # f'site:mercadolibre.com.mx "{colonia}" remate bancario "{region}"',
            # f'site:vivanuncios.com.mx "{colonia}" remate bancario "{region}"',
            f'site:propiedades.com/inmuebles/ "{colonia}" remate "{region}"',
            f'site:inmuebles24.com/propiedades/clasificado/ "{colonia}" remate "{region}"',
            f'site:lamudi.com.mx/detalle/ "{colonia}" remate "{region}"',
            f'site:mercadolibre.com.mx/MLM- "{colonia}" "remate bancario" "{region}"',
            f'site:vivanuncios.com.mx/a- "{colonia}" "remate bancario" "{region}"',
            # f'"{colonia}" "remate bancario" casa "{region}"',
            # f'"{colonia}" "casa en remate" "{region}"',
            # f'"{colonia}" "adjudicado" casa "{region}"',
            # f'"{colonia}" "listo para escriturar" casa "{region}"',
        ])

    return queries

# def build_queries(criteria: SearchCriteria) -> list[str]:
#     queries: list[str] = []

#     for colonia in criteria.colonias:
#         queries.extend(
#             [
#                 f'site:tiktok.com "{colonia}" remate bancario',
#                 f'site:instagram.com "{colonia}" remate bancario',
#                 f'site:facebook.com "{colonia}" remate bancario',
#                 f'"{colonia}" "remate bancario" casa CDMX',
#                 f'"{colonia}" "casa en remate" CDMX',
#                 f'"{colonia}" "adjudicado" "casa" CDMX',
#                 f'"{colonia}" "listo para escriturar" casa CDMX',
#                 f'site:propiedades.com "{colonia}" "casas remates"',
#                 f'site:inmuebles24.com "{colonia}" "remate" CDMX',
#                 f'site:lamudi.com.mx "{colonia}" "remate"',
#                 f'site:mercadolibre.com.mx "{colonia}" "remate bancario"',
#                 f'site:vivanuncios.com.mx "{colonia}" "remate bancario"',
#             ]
#         )

#     return queries