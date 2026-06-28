from __future__ import annotations

from playwright.sync_api import sync_playwright

from config import REQUEST_TIMEOUT_SECONDS
from models import PageContent
from fetchers.base import PageFetcher


class PlaywrightFetcher(PageFetcher):
    def fetch(self, url: str) -> PageContent:
        try:
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

                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=REQUEST_TIMEOUT_SECONDS * 1000,
                )

                page.wait_for_timeout(2000)

                title = page.title()
                text = page.locator("body").inner_text(timeout=5000)

                browser.close()

                return PageContent(
                    url=url,
                    title=title,
                    text=text[:12000],
                    status_code=200,
                )

        except Exception as exc:
            return PageContent(
                url=url,
                fetch_error=str(exc),
            )