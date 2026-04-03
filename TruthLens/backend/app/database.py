import json
import sqlite3
from pathlib import Path
from typing import Optional

from app.news_sources import get_seed_news

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "truthlens.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS news_articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        source_name TEXT NOT NULL,
        published_at TEXT NOT NULL,
        country TEXT NOT NULL,
        category TEXT NOT NULL,
        url TEXT UNIQUE NOT NULL,
        description TEXT NOT NULL,
        credibility_score INTEGER NOT NULL,
        credibility_label TEXT NOT NULL,
        explanation TEXT NOT NULL,
        batch_label TEXT,
        fetched_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        input_type TEXT NOT NULL,
        input_value TEXT NOT NULL,
        credibility_score INTEGER NOT NULL,
        credibility_label TEXT NOT NULL,
        explanation TEXT NOT NULL,
        risk_signals TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def seed_news_if_empty():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM news_articles")
    count = cursor.fetchone()["count"]

    if count == 0:
        upsert_news_items(cursor, get_seed_news(), "initial_seed")

    conn.commit()
    conn.close()


def upsert_news_items(cursor, items: list[dict], batch_label: str):
    for item in items:
        cursor.execute(
            """
            INSERT INTO news_articles (
                title, source_name, published_at, country, category, url,
                description, credibility_score, credibility_label, explanation, batch_label, fetched_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(url) DO UPDATE SET
                title = excluded.title,
                source_name = excluded.source_name,
                published_at = excluded.published_at,
                country = excluded.country,
                category = excluded.category,
                description = excluded.description,
                credibility_score = excluded.credibility_score,
                credibility_label = excluded.credibility_label,
                explanation = excluded.explanation,
                batch_label = excluded.batch_label,
                fetched_at = CURRENT_TIMESTAMP
            """,
            (
                item["title"],
                item["source_name"],
                item["published_at"],
                item["country"],
                item["category"],
                item["url"],
                item["description"],
                item["credibility_score"],
                item["credibility_label"],
                item["explanation"],
                batch_label,
            ),
        )


def refresh_news_batch(batch_label: str):
    conn = get_connection()
    cursor = conn.cursor()
    items = get_seed_news()
    cursor.execute("DELETE FROM news_articles")
    upsert_news_items(cursor, items, batch_label)
    cursor.execute("SELECT COUNT(*) as count FROM news_articles")
    total_rows = cursor.fetchone()["count"]
    conn.commit()
    conn.close()
    return total_rows


def get_news_from_db(country: Optional[str] = None, category: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM news_articles WHERE 1=1"
    params = []

    if country:
        query += " AND lower(country) = lower(?)"
        params.append(country)

    if category:
        query += " AND lower(category) = lower(?)"
        params.append(category)

    query += " ORDER BY published_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_categories_from_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT category FROM news_articles ORDER BY category ASC")
    rows = cursor.fetchall()
    conn.close()

    return [row["category"] for row in rows]


def save_user_check(input_type: str, input_value: str, result: dict):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO user_checks (
        input_type, input_value, credibility_score,
        credibility_label, explanation, risk_signals
    ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        input_type,
        input_value,
        result["credibility_score"],
        result["credibility_label"],
        result["explanation"],
        json.dumps(result["risk_signals"])
    ))

    conn.commit()
    conn.close()


def create_user(full_name: str, email: str, password_hash: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO users (full_name, email, password_hash)
    VALUES (?, ?, ?)
    """, (full_name, email.lower(), password_hash))

    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def get_user_by_email(email: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE lower(email) = lower(?)", (email,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def get_user_by_id(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None
