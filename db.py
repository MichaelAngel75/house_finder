from sqlalchemy import create_engine, text
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)


def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portal TEXT,
                title TEXT,
                price INTEGER,
                location TEXT,
                bedrooms INTEGER,
                bathrooms INTEGER,
                description TEXT,
                url TEXT UNIQUE,
                is_remate INTEGER,
                remate_stage TEXT,
                risk_level TEXT,
                include INTEGER,
                reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))


def listing_exists(url: str) -> bool:
    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT 1 FROM listings WHERE url = :url LIMIT 1"),
            {"url": url}
        ).fetchone()
        return result is not None


def save_listing(item):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT OR IGNORE INTO listings (
                portal, title, price, location, bedrooms, bathrooms,
                description, url, is_remate, remate_stage, risk_level,
                include, reason
            )
            VALUES (
                :portal, :title, :price, :location, :bedrooms, :bathrooms,
                :description, :url, :is_remate, :remate_stage, :risk_level,
                :include, :reason
            )
        """), {
            "portal": item.portal,
            "title": item.title,
            "price": item.price,
            "location": item.location,
            "bedrooms": item.bedrooms,
            "bathrooms": item.bathrooms,
            "description": item.description,
            "url": item.url,
            "is_remate": int(item.is_remate),
            "remate_stage": item.remate_stage,
            "risk_level": item.risk_level,
            "include": int(item.include),
            "reason": item.reason,
        })