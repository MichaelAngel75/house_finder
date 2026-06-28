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
            result.model_dump(),
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
                **item.model_dump(exclude={"created_at"}),
                "is_remate": int(item.is_remate),
                "include": int(item.include),
                "red_flags": "|".join(item.red_flags),
            },
        )