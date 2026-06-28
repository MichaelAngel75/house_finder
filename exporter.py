from __future__ import annotations

import pandas as pd
from models import Classification


def _to_dataframe(items: list[Classification]) -> pd.DataFrame:
    rows = []

    for item in items:
        row = item.model_dump()
        row["red_flags"] = "|".join(item.red_flags)
        rows.append(row)

    if not rows:
        return pd.DataFrame(
            columns=[
                "criteria_id",
                "query",
                "title",
                "snippet",
                "url",
                "source_domain",
                "is_remate",
                "remate_stage",
                "risk_level",
                "include",
                "confidence",
                "reason",
                "red_flags",
                "created_at",
            ]
        )

    return pd.DataFrame(rows)


def export_debug(
    items: list[Classification],
    filename: str,
):
    """
    Export EVERYTHING.
    Useful for debugging.
    """

    df = _to_dataframe(items)

    df.to_csv(filename, index=False)


def export_filtered(
    items: list[Classification],
    filename: str,
):
    """
    Export only approved houses.
    """

    filtered = [
        item
        for item in items
        if item.include
    ]

    df = _to_dataframe(filtered)

    df.to_csv(filename, index=False)