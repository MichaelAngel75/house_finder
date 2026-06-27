
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin

from config import (
    MAX_PAGES_PER_SITE,
    MAX_RESULTS_PER_SITE,
    REQUEST_TIMEOUT_SECONDS,
    DELAY_BETWEEN_REQUESTS_SECONDS,
)
from models import SearchCriteria, Listing
from filters import parse_price
from connectors.base import BaseConnector


class PropiedadesConnector(BaseConnector):
    portal_name = "Propiedades.com"
    base_url = "https://propiedades.com"

    def slugify_colonia(self, colonia: str) -> str:
        return (
            colonia.lower()
            .strip()
            .replace(" ", "-")
            .replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
            .replace("ñ", "n")
        )

    def build_candidate_urls(self, colonia: str, page: int) -> list[str]:
        slug = self.slugify_colonia(colonia)

        urls = [
            f"{self.base_url}/{slug}/casas-remates",
            f"{self.base_url}/{slug}-df/casas-remates",
            f"{self.base_url}/{slug}/casas-venta",
            f"{self.base_url}/{slug}-df/casas-venta",
        ]

        if page > 1:
            urls = [f"{url}?pagina={page}" for url in urls]

        return urls

    def looks_like_listing_url(self, href: str) -> bool:
        if not href:
            return False

        bad_patterns = [
            "login",
            "registro",
            "contacto",
            "publicar",
            "blog",
            "aviso",
            "privacidad",
            "terminos",
        ]

        if any(pattern in href.lower() for pattern in bad_patterns):
            return False

        return True

    def extract_bedrooms(self, text: str) -> int | None:
        match = re.search(r"(\d+)\s*rec", text.lower())
        return int(match.group(1)) if match else None

    def extract_bathrooms(self, text: str) -> int | None:
        match = re.search(r"(\d+)\s*bañ", text.lower())
        return int(match.group(1)) if match else None

    def search(self, criteria: SearchCriteria) -> list[Listing]:
        results: list[Listing] = []
        seen_urls = set()

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
        }

        for colonia in criteria.colonias:
            for page in range(1, MAX_PAGES_PER_SITE + 1):
                candidate_urls = self.build_candidate_urls(colonia, page)

                for search_url in candidate_urls:
                    if len(results) >= MAX_RESULTS_PER_SITE:
                        return results

                    print(f"Fetching: {search_url}")

                    try:
                        response = requests.get(
                            search_url,
                            headers=headers,
                            timeout=REQUEST_TIMEOUT_SECONDS,
                        )

                        print(f"Status: {response.status_code}, bytes: {len(response.text)}")

                        if response.status_code != 200:
                            continue

                    except requests.RequestException as e:
                        print(f"Request failed: {e}")
                        continue

                    soup = BeautifulSoup(response.text, "html.parser")

                    links = soup.select("a[href]")
                    print(f"Links found: {len(links)}")

                    for link in links:
                        href = link.get("href")
                        if not href:
                            continue

                        full_url = urljoin(self.base_url, href)

                        if full_url in seen_urls:
                            continue

                        if "propiedades.com" not in full_url:
                            continue

                        if not self.looks_like_listing_url(full_url):
                            continue

                        text = link.get_text(" ", strip=True)

                        if not text or len(text) < 15:
                            continue

                        text_lower = text.lower()

                        possible_listing = (
                            "remate" in text_lower
                            or "recámara" in text_lower
                            or "recamaras" in text_lower
                            or "baño" in text_lower
                            or "mxn" in text_lower
                            or "$" in text_lower
                        )

                        if not possible_listing:
                            continue

                        seen_urls.add(full_url)

                        listing = Listing(
                            portal=self.portal_name,
                            title=text[:180],
                            price=parse_price(text),
                            location=colonia,
                            bedrooms=self.extract_bedrooms(text),
                            bathrooms=self.extract_bathrooms(text),
                            description=text,
                            url=full_url,
                        )

                        results.append(listing)

                    time.sleep(DELAY_BETWEEN_REQUESTS_SECONDS)

        return results
# https://propiedades.com/portales/casas-remates
# https://propiedades.com/portales-sur-df/casas-remates
# https://propiedades.com/portales-norte-df/casas-venta

# import time
# import requests
# from bs4 import BeautifulSoup
# from urllib.parse import quote_plus

# from config import (
#     MAX_PAGES_PER_SITE,
#     MAX_RESULTS_PER_SITE,
#     REQUEST_TIMEOUT_SECONDS,
#     DELAY_BETWEEN_REQUESTS_SECONDS,
# )
# from models import SearchCriteria, Listing
# from filters import parse_price
# from connectors.base import BaseConnector


# class PropiedadesConnector(BaseConnector):
#     portal_name = "Propiedades.com"

#     def build_url(self, criteria: SearchCriteria, colonia: str, page: int) -> str:
#         operation = "venta" if criteria.operacion.lower() == "compra" else "renta"
#         query = quote_plus(colonia)

#         # URL base aproximada. Puede requerir ajuste según estructura actual del sitio.
#         return f"https://propiedades.com/{query}/{operation}-casas?pagina={page}"

#     def search(self, criteria: SearchCriteria) -> list[Listing]:
#         results: list[Listing] = []

#         headers = {
#             "User-Agent": "Mozilla/5.0 compatible; LocalResearchBot/1.0"
#         }

#         for colonia in criteria.colonias:
#             for page in range(1, MAX_PAGES_PER_SITE + 1):
#                 if len(results) >= MAX_RESULTS_PER_SITE:
#                     return results

#                 url = self.build_url(criteria, colonia, page)

#                 try:
#                     response = requests.get(
#                         url,
#                         headers=headers,
#                         timeout=REQUEST_TIMEOUT_SECONDS
#                     )
#                     response.raise_for_status()
#                 except requests.RequestException:
#                     continue

#                 soup = BeautifulSoup(response.text, "html.parser")

#                 cards = soup.select("a[href*='/propiedades/'], a[href*='/inmuebles/']")

#                 seen_urls = set()

#                 for card in cards:
#                     href = card.get("href")
#                     if not href:
#                         continue

#                     if href.startswith("/"):
#                         href = "https://propiedades.com" + href

#                     if href in seen_urls:
#                         continue

#                     seen_urls.add(href)

#                     text = card.get_text(" ", strip=True)
#                     if not text or len(text) < 20:
#                         continue

#                     listing = Listing(
#                         portal=self.portal_name,
#                         title=text[:180],
#                         price=parse_price(text),
#                         location=colonia,
#                         bedrooms=None,
#                         bathrooms=None,
#                         description=text,
#                         url=href,
#                     )

#                     results.append(listing)

#                 time.sleep(DELAY_BETWEEN_REQUESTS_SECONDS)

#         return results