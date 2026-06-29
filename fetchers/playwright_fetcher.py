from __future__ import annotations

from playwright.sync_api import sync_playwright

from config import REQUEST_TIMEOUT_SECONDS
from models import PageContent
from fetchers.base import PageFetcher


class PlaywrightFetcher(PageFetcher):
    def fetch(self, url: str) -> PageContent:
        browser = None

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
                    viewport={"width": 1440, "height": 1200},
                )

                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=REQUEST_TIMEOUT_SECONDS * 1000,
                )

                # Give JS-heavy real-estate pages time to hydrate/render.
                page.wait_for_timeout(4000)

                try:
                    page.wait_for_load_state(
                        "networkidle",
                        timeout=REQUEST_TIMEOUT_SECONDS * 1000,
                    )
                except Exception:
                    # Some sites never become fully idle because of analytics/ads.
                    pass

                title = page.title() or ""
                html = page.content() or ""

                try:
                    text = page.locator("body").inner_text(timeout=10000)
                except Exception:
                    text = ""

                browser.close()

                return PageContent(
                    url=url,
                    title=title,
                    text=text[:20000],
                    html=html[:300000],
                    status_code=200,
                    fetch_error=None,
                )

        except Exception as exc:
            if browser:
                try:
                    browser.close()
                except Exception:
                    pass

            return PageContent(
                url=url,
                title="",
                text="",
                html="",
                status_code=None,
                fetch_error=str(exc),
            )