import re
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from models import SearchCriteria, Listing
from filters import parse_price
from connectors.base import BaseConnector


class PropiedadesPlaywrightConnector(BaseConnector):
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

    def build_urls(self, colonia: str) -> list[str]:
        slug = self.slugify_colonia(colonia)
        return [
            f"{self.base_url}/{slug}/casas-remates",
            f"{self.base_url}/{slug}/casas-venta",
        ]

    def extract_bedrooms(self, text: str) -> int | None:
        match = re.search(r"(\d+)\s*rec", text.lower())
        return int(match.group(1)) if match else None

    def extract_bathrooms(self, text: str) -> int | None:
        match = re.search(r"(\d+)\s*bañ", text.lower())
        return int(match.group(1)) if match else None

    def search(self, criteria: SearchCriteria) -> list[Listing]:
        results = []
        seen_urls = set()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="es-MX",
            )

            for colonia in criteria.colonias:
                for url in self.build_urls(colonia):
                    print(f"Playwright fetching: {url}")

                    try:
                        page.goto(url, wait_until="domcontentloaded", timeout=20000)
                        page.wait_for_timeout(3000)
                    except PlaywrightTimeoutError:
                        print(f"Timeout: {url}")
                        continue
                    except Exception as e:
                        print(f"Playwright error: {e}")
                        continue

                    links = page.locator("a[href]").all()
                    print(f"Links found: {len(links)}")

                    for link in links:
                        try:
                            href = link.get_attribute("href")
                            text = link.inner_text(timeout=1000).strip()
                        except Exception:
                            continue

                        if not href or not text or len(text) < 15:
                            continue

                        full_url = urljoin(self.base_url, href)

                        if full_url in seen_urls:
                            continue

                        if "propiedades.com" not in full_url:
                            continue

                        text_lower = text.lower()

                        possible_listing = (
                            "remate" in text_lower
                            or "$" in text_lower
                            or "recámara" in text_lower
                            or "recamaras" in text_lower
                            or "baño" in text_lower
                        )

                        if not possible_listing:
                            continue

                        seen_urls.add(full_url)

                        results.append(
                            Listing(
                                portal=self.portal_name,
                                title=text[:180],
                                price=parse_price(text),
                                location=colonia,
                                bedrooms=self.extract_bedrooms(text),
                                bathrooms=self.extract_bathrooms(text),
                                description=text,
                                url=full_url,
                            )
                        )

            browser.close()

        return results