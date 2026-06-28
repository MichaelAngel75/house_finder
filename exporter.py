from __future__ import annotations

import pandas as pd
from models import Classification


def export_classifications(items: list[Classification], output_file: str) -> None:
    rows = []

    for item in items:
        row = item.model_dump()
        row["red_flags"] = "|".join(item.red_flags)
        rows.append(row)

    df = pd.DataFrame(rows)

    if df.empty:
        df = pd.DataFrame(
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

    df.to_csv(output_file, index=False)