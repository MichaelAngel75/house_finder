from __future__ import annotations

from sqlalchemy import create_engine, text
from config import DATABASE_URL
from models import SearchCriteria, SearchResult, Classification

engine = create_engine(DATABASE_URL, future=True)


def init_db() -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS search_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'started'
                )
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS criteria (
                    criteria_id TEXT PRIMARY KEY,
                    operacion TEXT,
                    rango_min INTEGER,
                    rango_max INTEGER,
                    recamaras INTEGER,
                    banios INTEGER,
                    colonias TEXT
                )
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS candidate_urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    criteria_id TEXT,
                    query TEXT,
                    title TEXT,
                    snippet TEXT,
                    url TEXT UNIQUE,
                    source_domain TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS classifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    criteria_id TEXT,
                    query TEXT,
                    title TEXT,
                    snippet TEXT,
                    url TEXT UNIQUE,
                    source_domain TEXT,
                    price INTEGER,
                    price_source TEXT,
                    location TEXT,
                    bedrooms INTEGER,
                    bathrooms INTEGER,
                    is_remate INTEGER,
                    remate_stage TEXT,
                    risk_level TEXT,
                    include INTEGER,
                    confidence REAL,
                    reason TEXT,
                    red_flags TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )

        migrate_classifications_table(conn)


def migrate_classifications_table(conn) -> None:
    """
    SQLite CREATE TABLE IF NOT EXISTS does not add new columns to an existing table.
    This migration safely adds columns that were introduced after the first version.
    """

    existing_columns = {
        row[1]
        for row in conn.execute(text("PRAGMA table_info(classifications)")).fetchall()
    }

    required_columns = {
        "price": "INTEGER",
        "price_source": "TEXT",
        "location": "TEXT",
        "bedrooms": "INTEGER",
        "bathrooms": "INTEGER",
    }

    for column_name, column_type in required_columns.items():
        if column_name not in existing_columns:
            conn.execute(
                text(
                    f"ALTER TABLE classifications ADD COLUMN {column_name} {column_type}"
                )
            )


def create_run() -> int:
    with engine.begin() as conn:
        result = conn.execute(
            text("INSERT INTO search_runs(status) VALUES ('started')")
        )
        return int(result.lastrowid)


def finish_run(run_id: int, status: str = "finished") -> None:
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE search_runs SET status = :status WHERE id = :id"),
            {"status": status, "id": run_id},
        )


def save_criteria(criteria: SearchCriteria) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT OR REPLACE INTO criteria (
                    criteria_id,
                    operacion,
                    rango_min,
                    rango_max,
                    recamaras,
                    banios,
                    colonias
                )
                VALUES (
                    :criteria_id,
                    :operacion,
                    :rango_min,
                    :rango_max,
                    :recamaras,
                    :banios,
                    :colonias
                )
                """
            ),
            {
                "criteria_id": criteria.criteria_id,
                "operacion": criteria.operacion,
                "rango_min": criteria.rango_min,
                "rango_max": criteria.rango_max,
                "recamaras": criteria.recamaras,
                "banios": criteria.banios,
                "colonias": "|".join(criteria.colonias),
            },
        )


def candidate_exists(url: str) -> bool:
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT 1 FROM candidate_urls WHERE url = :url LIMIT 1"),
            {"url": url},
        ).fetchone()
        return row is not None


def classification_exists(url: str) -> bool:
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT 1 FROM classifications WHERE url = :url LIMIT 1"),
            {"url": url},
        ).fetchone()
        return row is not None


def save_candidate(result: SearchResult) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT OR IGNORE INTO candidate_urls (
                    criteria_id,
                    query,
                    title,
                    snippet,
                    url,
                    source_domain
                )
                VALUES (
                    :criteria_id,
                    :query,
                    :title,
                    :snippet,
                    :url,
                    :source_domain
                )
                """
            ),
            {
                "criteria_id": result.criteria_id,
                "query": result.query,
                "title": result.title,
                "snippet": result.snippet,
                "url": result.url,
                "source_domain": result.source_domain,
            },
        )


def save_classification(item: Classification) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT OR REPLACE INTO classifications (
                    criteria_id,
                    query,
                    title,
                    snippet,
                    url,
                    source_domain,
                    price,
                    price_source,
                    location,
                    bedrooms,
                    bathrooms,
                    is_remate,
                    remate_stage,
                    risk_level,
                    include,
                    confidence,
                    reason,
                    red_flags
                )
                VALUES (
                    :criteria_id,
                    :query,
                    :title,
                    :snippet,
                    :url,
                    :source_domain,
                    :price,
                    :price_source,
                    :location,
                    :bedrooms,
                    :bathrooms,
                    :is_remate,
                    :remate_stage,
                    :risk_level,
                    :include,
                    :confidence,
                    :reason,
                    :red_flags
                )
                """
            ),
            {
                "criteria_id": item.criteria_id,
                "query": item.query,
                "title": item.title,
                "snippet": item.snippet,
                "url": item.url,
                "source_domain": item.source_domain,
                "price": item.price,
                "price_source": item.price_source,
                "location": item.location,
                "bedrooms": item.bedrooms,
                "bathrooms": item.bathrooms,
                "is_remate": int(item.is_remate),
                "remate_stage": item.remate_stage,
                "risk_level": item.risk_level,
                "include": int(item.include),
                "confidence": item.confidence,
                "reason": item.reason,
                "red_flags": "|".join(item.red_flags),
            },
        )