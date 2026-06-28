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

app = typer.Typer(add_completion=False)


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
            )
        )

    return criteria_list


@app.callback(invoke_without_command=True)
def run(
    input_file: str = typer.Option("input.csv", help="CSV input file."),
    output_file: str = typer.Option("output.csv", help="CSV output file."),
):
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

                results = provider.search(
                    query=query,
                    criteria_id=criteria.criteria_id,
                )

                for result in results:
                    if discovered_count >= MAX_URLS_PER_CRITERIA:
                        break

                    result = enrich_search_result(result)
                    if result.url in seen_in_criteria:
                        continue

                    seen_in_criteria.add(result.url)

                    if not candidate_exists(result.url):
                        save_candidate(result)
                        print(f"  [green]Candidate:[/green] {result.url}")
                    else:
                        print(f"  [yellow]Cached candidate:[/yellow] {result.url}")

                    if classification_exists(result.url):
                        print(f"  [yellow]Already classified:[/yellow] {result.url}")
                        continue

                    page = None

                    if ENABLE_LIVE_FETCH:
                        page = requests_fetcher.fetch(result.url)

                        if page.fetch_error and playwright_fetcher:
                            page = playwright_fetcher.fetch(result.url)

                    classified = llm_classify(result, page)
                    save_classification(classified)
                    final_items.append(classified)

                    discovered_count += 1

                time.sleep(DELAY_BETWEEN_REQUESTS_SECONDS)

        export_filtered(
            final_items,
            output_file,
        )

        debug_file = output_file.replace(
            ".csv",
            "_debug.csv",
        )

        export_debug(
            final_items,
            debug_file,
        )
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
        print(f"[bold red]Run failed:[/bold red] {exc}")
        raise


if __name__ == "__main__":
    app()