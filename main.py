from __future__ import annotations

import hashlib
import time

import pandas as pd
import typer
from rich import print

from config import (
    SEARCH_PROVIDER,
    MAX_URLS_PER_CRITERIA,
    DELAY_BETWEEN_REQUESTS_SECONDS,
    ENABLE_LIVE_FETCH,
    ENABLE_PLAYWRIGHT_FALLBACK,
)
from models import SearchCriteria, Classification
from database import (
    init_db,
    create_run,
    finish_run,
    save_criteria,
    save_candidate,
    save_classification,
    candidate_exists,
    classification_exists,
)
from query_builder import build_queries
from classifier import llm_classify
from exporter import (
    export_debug,
    export_filtered,
)
from search_providers import get_search_provider
from fetchers.requests_fetcher import RequestsFetcher
from fetchers.playwright_fetcher import PlaywrightFetcher
from listing_parser import enrich_search_result
from url_tools.registry import get_resolver
from pathlib import Path

from app_logger import setup_logging, get_logger, log_input, log_output, log_event, log_error

logger = get_logger(__name__)


app = typer.Typer(add_completion=False)


def get_page_html(page) -> str | None:
    if page is None:
        return None

    for attr in ("html", "content", "text", "body", "raw_html"):
        value = getattr(page, attr, None)
        if value:
            return value

    if hasattr(page, "model_dump"):
        data = page.model_dump()
        for key in ("html", "content", "text", "body", "raw_html"):
            value = data.get(key)
            if value:
                return value

    return None


JS_HEAVY_DOMAINS = (
    # "propiedades.com",
    "inmuebles24.com",
    "lamudi.com.mx",
)


def fetch_page_with_fallback(
    url: str,
    requests_fetcher: RequestsFetcher,
    playwright_fetcher: PlaywrightFetcher | None,
    label: str,
):
    page = None
    html = None

    if not ENABLE_LIVE_FETCH:
        return page, html

    force_playwright = any(domain in url.lower() for domain in JS_HEAVY_DOMAINS)

    if force_playwright and playwright_fetcher:
        log_event(logger, "Fetching %s URL with Playwright: %s", label, url)
        page = playwright_fetcher.fetch(url)
        log_output(logger, f"{label} playwright fetch page", page)

        html = get_page_html(page)
        fetch_error = getattr(page, "fetch_error", None)

        if html and not fetch_error:
            return page, html

        log_event(
            logger,
            "Playwright failed or empty for %s URL, trying requests: %s",
            label,
            url,
        )

    log_event(logger, "Fetching %s URL with requests: %s", label, url)
    page = requests_fetcher.fetch(url)
    log_output(logger, f"{label} requests fetch page", page)

    html = get_page_html(page)
    fetch_error = getattr(page, "fetch_error", None)

    if html and not fetch_error:
        return page, html

    if playwright_fetcher and not force_playwright:
        log_event(logger, "Using Playwright fallback for %s URL: %s", label, url)
        page = playwright_fetcher.fetch(url)
        log_output(logger, f"{label} playwright fallback fetch page", page)
        html = get_page_html(page)

        if html:
            return page, html

    log_event(
        logger,
        "Both fetchers failed or returned empty content for %s URL: %s",
        label,
        url,
    )

    return page, html

# def fetch_page_with_fallback(
#     url: str,
#     requests_fetcher: RequestsFetcher,
#     playwright_fetcher: PlaywrightFetcher | None,
#     label: str,
# ):
#     page = None
#     html = None

#     if not ENABLE_LIVE_FETCH:
#         return page, html

#     log_event(logger, "Fetching %s URL: %s", label, url)
#     page = requests_fetcher.fetch(url)
#     log_output(logger, f"{label} requests fetch page", page)

#     html = get_page_html(page)

#     fetch_error = getattr(page, "fetch_error", None)

#     if playwright_fetcher and (fetch_error or not html):
#         log_event(logger, "Using Playwright fallback for %s URL: %s", label, url)
#         page = playwright_fetcher.fetch(url)
#         log_output(logger, f"{label} playwright fetch page", page)
#         html = get_page_html(page)

#     return page, html

def make_criteria_id(row_index: int, row: pd.Series) -> str:
    raw = "|".join(str(value) for value in row.values)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]
    return f"criteria_{row_index}_{digest}"


def load_criteria(input_file: str) -> list[SearchCriteria]:
    df = pd.read_csv(input_file)

    required = [
        "operacion",
        "rango_min",
        "rango_max",
        "recamaras",
        "banios",
        "colonias",
        "state",
    ]

    missing = [column for column in required if column not in df.columns]

    if missing:
        raise ValueError(f"Missing required input columns: {missing}")

    criteria_list: list[SearchCriteria] = []

    for index, row in df.iterrows():
        colonias = [
            colonia.strip()
            for colonia in str(row["colonias"]).split("|")
            if colonia.strip()
        ]

        criteria_list.append(
            SearchCriteria(
                criteria_id=make_criteria_id(index, row),
                operacion=str(row["operacion"]).strip().lower(),
                rango_min=int(row["rango_min"]),
                rango_max=int(row["rango_max"]),
                recamaras=None
                if pd.isna(row["recamaras"])
                else int(row["recamaras"]),
                banios=None
                if pd.isna(row["banios"])
                else int(row["banios"]),
                colonias=colonias,
                state=str(row["state"]).strip()
            )
        )

    return criteria_list


@app.callback(invoke_without_command=True)
def run(
    input_file: str = typer.Option("input.csv", help="CSV input file."),
    output_file: str = typer.Option("output.csv", help="CSV output file."),
):

    setup_logging()

    log_event(logger, "House finding run started")
    log_input(logger, "input_file", input_file)
    log_input(logger, "output_file", output_file)

    init_db()
    run_id = create_run()
    final_items: list[Classification] = []


    try:
        criteria_list = load_criteria(input_file)
        provider = get_search_provider(SEARCH_PROVIDER)

        requests_fetcher = RequestsFetcher()
        playwright_fetcher = (
            PlaywrightFetcher() if ENABLE_PLAYWRIGHT_FALLBACK else None
        )

        print(f"[bold blue]Search provider:[/bold blue] {SEARCH_PROVIDER}")
        print(f"[bold blue]Live page fetch enabled:[/bold blue] {ENABLE_LIVE_FETCH}")

        for criteria in criteria_list:
            print(f"\n[bold green]Criteria:[/bold green] {criteria}")
            save_criteria(criteria)

            queries = build_queries(criteria)

            discovered_count = 0
            seen_in_criteria: set[str] = set()

            for query in queries:
                if discovered_count >= MAX_URLS_PER_CRITERIA:
                    break

                print(f"[cyan]Query:[/cyan] {query}")
                log_input(logger, "search query", query)

                results = provider.search(
                    query=query,
                    criteria_id=criteria.criteria_id,
                )

                log_output(logger, "search results", results)                


                for result in results:
                    if discovered_count >= MAX_URLS_PER_CRITERIA:
                        break

                    # # result = enrich_search_result(result)
                    # # if result.url in seen_in_criteria:
                    # #     continue

                    # result = enrich_search_result(result)
                    # seen_in_criteria.add(result.url)
                    # page = None
                    # if ENABLE_LIVE_FETCH:
                    #     log_event(logger, "Fetching search result URL: %s", result.url)
                    #     page = requests_fetcher.fetch(result.url)
                    #     log_output(logger, "search result fetch page", page)
                    #     if page.fetch_error and playwright_fetcher:
                    #         log_event(logger, "Using Playwright fallback for: %s", result.url)
                    #         page = playwright_fetcher.fetch(result.url)
                    #         log_output(logger, "playwright search result fetch page", page)
                    # html = page.html if page else None

                    result = enrich_search_result(result)

                    page, html = fetch_page_with_fallback(
                        url=result.url,
                        requests_fetcher=requests_fetcher,
                        playwright_fetcher=playwright_fetcher,
                        label="search result",
                    )

                    resolver = get_resolver(result.url)
                    property_urls = resolver.resolve(result.url, html)

                    log_output(logger, "resolved property URLs", property_urls)

                    if not property_urls:
                        print(f"  [yellow]No property URLs resolved:[/yellow] {result.url}")
                        continue

                    for property_url in property_urls:
                        if discovered_count >= MAX_URLS_PER_CRITERIA:
                            break

                        if property_url in seen_in_criteria:
                            continue

                        log_event(logger, "Resolved property URL: %s", property_url)
                        seen_in_criteria.add(property_url)

                        property_result = result.model_copy(update={"url": property_url})

                        if not candidate_exists(property_url):
                            # TODO: validate this is good
                            # save_candidate(result)
                            save_candidate(property_result)

                            print(f"  [green]Property candidate:[/green] {property_url}")
                        else:
                            print(f"  [yellow]Cached property candidate:[/yellow] {property_url}")

                        if classification_exists(property_url):
                            print(f"  [yellow]Already classified:[/yellow] {property_url}")
                            continue

                        # property_page = None
                        # if ENABLE_LIVE_FETCH:
                        #     log_event(logger, "Fetching property URL: %s", property_url)
                        #     property_page = requests_fetcher.fetch(property_url)
                        #     log_output(logger, "property fetch page", property_page)
                        #     if property_page.fetch_error and playwright_fetcher:
                        #         log_event(logger, "Using Playwright fallback for property: %s", property_url)
                        #         property_page = playwright_fetcher.fetch(property_url)
                        #         log_output(logger, "playwright property fetch page", property_page)
                        # log_input(logger, "llm input result", property_result)
                        # log_input(logger, "llm input page", property_page)
                        property_page, _ = fetch_page_with_fallback(
                                                url=property_url,
                                                requests_fetcher=requests_fetcher,
                                                playwright_fetcher=playwright_fetcher,
                                                label="property",
                                            )

                        # TODO: validate this is good
                        # classified = llm_classify(result, property_page)
                        # classified = llm_classify(property_result, property_page)
                        classified = llm_classify(property_result, criteria, property_page)

                        log_output(logger, "llm classification", classified)

                        save_classification(classified)
                        final_items.append(classified)

                        discovered_count += 1

                time.sleep(DELAY_BETWEEN_REQUESTS_SECONDS)

        export_filtered(final_items, output_file)
        # debug_file = output_file.replace(".csv", "_debug.csv")
        output_path = Path(output_file)
        debug_file = str(output_path.with_name(f"{output_path.stem}_debug{output_path.suffix}"))
        export_debug(final_items, debug_file)
        
        finish_run(run_id, "finished")

        print(f"\n[bold green]Output written:[/bold green] {output_file}")
        approved = len(
            [x for x in final_items if x.include]
        )

        rejected = len(final_items) - approved

        print()

        print(f"Approved houses : {approved}")
        print(f"Rejected houses : {rejected}")

        print()

        print(f"Filtered output : {output_file}")
        print(f"Debug output    : {debug_file}")        

    except Exception as exc:
        finish_run(run_id, "failed")
        log_error(logger, "House finding run failed")
        print(f"[bold red]Run failed:[/bold red] {exc}")
        raise    


if __name__ == "__main__":
    app()