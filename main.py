import pandas as pd
import typer
from rich import print

from models import SearchCriteria
from db import init_db, listing_exists, save_listing
from filters import (
    matches_criteria,
    looks_like_remate_candidate,
    has_high_risk_words,
)
from llm_classifier import classify_listing
from connectors import ALL_CONNECTORS

app = typer.Typer()


def load_criteria(input_file: str) -> list[SearchCriteria]:
    df = pd.read_csv(input_file)
    criteria_list = []

    required_columns = [
        "operacion",
        "rango_min",
        "rango_max",
        "recamaras",
        "banios",
        "colonias",
    ]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    for _, row in df.iterrows():
        colonias = [
            c.strip()
            for c in str(row["colonias"]).split("|")
            if c.strip()
        ]

        criteria = SearchCriteria(
            operacion=str(row["operacion"]).strip(),
            rango_min=int(row["rango_min"]),
            rango_max=int(row["rango_max"]),
            recamaras=int(row["recamaras"]) if not pd.isna(row["recamaras"]) else None,
            banios=int(row["banios"]) if not pd.isna(row["banios"]) else None,
            colonias=colonias,
        )

        criteria_list.append(criteria)

    return criteria_list


@app.command()
def run(
    input_file: str = "input.csv",
    output_file: str = "output.csv",
):
    init_db()

    all_final_rows = []
    criteria_list = load_criteria(input_file)

    for criteria in criteria_list:
        print(f"[bold blue]Searching criteria:[/bold blue] {criteria}")

        for connector in ALL_CONNECTORS:
            print(f"[green]Running connector:[/green] {connector.portal_name}")

            listings = connector.search(criteria)
            print(f"Found raw listings: {len(listings)}")

            for listing in listings:
                if listing_exists(listing.url):
                    continue

                if not matches_criteria(listing, criteria):
                    continue

                if has_high_risk_words(listing):
                    continue

                if not looks_like_remate_candidate(listing):
                    continue

                classified = classify_listing(listing)

                save_listing(classified)

                if classified.include:
                    all_final_rows.append(classified.model_dump())

    if all_final_rows:
        df = pd.DataFrame(all_final_rows)
        df.to_csv(output_file, index=False)
        print(f"[bold green]Output created:[/bold green] {output_file}")
    else:
        print("[yellow]No qualifying low-risk remate listings found.[/yellow]")


if __name__ == "__main__":
    app()