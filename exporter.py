from __future__ import annotations

from pathlib import Path

import pandas as pd
from models import Classification


EXPORT_COLUMNS = [
    "criteria_id",
    "query",
    "title",
    "snippet",
    "url",
    "source_domain",
    "price",
    "price_source",
    "location",
    "bedrooms",
    "bathrooms",
    "is_remate",
    "remate_stage",
    "risk_level",
    "include",
    "matches_price_range",
    "matches_bedrooms",
    "matches_bathrooms",
    "matches_location",
    "confidence",
    "reason",
    "red_flags",
    "created_at",
]


def _to_dataframe(items: list[Classification]) -> pd.DataFrame:
    rows = []

    for item in items:
        row = item.model_dump()
        row["red_flags"] = "|".join(item.red_flags)
        rows.append(row)

    df = pd.DataFrame(rows)

    if df.empty:
        return pd.DataFrame(columns=EXPORT_COLUMNS)

    for column in EXPORT_COLUMNS:
        if column not in df.columns:
            df[column] = None

    return df[EXPORT_COLUMNS]


def _format_excel(writer: pd.ExcelWriter, sheet_name: str, df: pd.DataFrame) -> None:
    worksheet = writer.sheets[sheet_name]

    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions

    widths = {
        "A": 18,
        "B": 45,
        "C": 45,
        "D": 60,
        "E": 70,
        "F": 25,
        "G": 14,
        "H": 16,
        "I": 28,
        "J": 12,
        "K": 12,
        "L": 12,
        "M": 24,
        "N": 16,
        "O": 10,
        "P": 18,
        "Q": 18,
        "R": 18,
        "S": 18,
        "T": 12,
        "U": 70,
        "V": 40,
        "W": 24,
    }

    for col, width in widths.items():
        worksheet.column_dimensions[col].width = width

    for row in worksheet.iter_rows():
        for cell in row:
            cell.alignment = cell.alignment.copy(wrap_text=True, vertical="top")

    if "price" in df.columns:
        for cell in worksheet["G"][1:]:
            cell.number_format = '$#,##0'

    if "confidence" in df.columns:
        for cell in worksheet["T"][1:]:
            cell.number_format = '0.00'


def export_debug(
    items: list[Classification],
    filename: str,
):
    df = _to_dataframe(items)
    df.to_csv(filename, index=False, encoding="utf-8-sig")

    xlsx_filename = str(Path(filename).with_suffix(".xlsx"))

    with pd.ExcelWriter(xlsx_filename, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Debug", index=False)
        _format_excel(writer, "Debug", df)


def export_filtered(
    items: list[Classification],
    filename: str,
):
    filtered = [item for item in items if item.include]

    df = _to_dataframe(filtered)
    df.to_csv(filename, index=False, encoding="utf-8-sig")

    xlsx_filename = str(Path(filename).with_suffix(".xlsx"))

    with pd.ExcelWriter(xlsx_filename, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Approved", index=False)
        _format_excel(writer, "Approved", df)