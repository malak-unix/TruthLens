import json
import sqlite3
from pathlib import Path
from typing import Optional

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
        source_type TEXT,
        source_trust_level TEXT,
        language TEXT,
        batch_label TEXT,
        fetched_at TEXT DEFAULT CURRENT_TIMESTAMP,
        analyzed_at TEXT DEFAULT CURRENT_TIMESTAMP
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
    CREATE TABLE IF NOT EXISTS refresh_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_label TEXT NOT NULL,
        started_at TEXT NOT NULL,
        finished_at TEXT NOT NULL,
        inserted_count INTEGER NOT NULL,
        duplicate_count INTEGER NOT NULL,
        failed_source_count INTEGER NOT NULL,
        trend_update_count INTEGER NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trending_topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT NOT NULL,
        region TEXT NOT NULL,
        intensity INTEGER NOT NULL,
        article_count INTEGER NOT NULL,
        freshness TEXT NOT NULL,
        credibility_warning INTEGER NOT NULL DEFAULT 0,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
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


def upsert_news_items(cursor, items: list[dict], batch_label: str):
    inserted = 0
    duplicates = 0

    for item in items:
        cursor.execute("SELECT id FROM news_articles WHERE url = ?", (item["url"],))
        existing = cursor.fetchone()

        cursor.execute(
            """
            INSERT INTO news_articles (
                title, source_name, published_at, country, category, url,
                description, credibility_score, credibility_label, explanation,
                source_type, source_trust_level, language, batch_label, fetched_at, analyzed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
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
                source_type = excluded.source_type,
                source_trust_level = excluded.source_trust_level,
                language = excluded.language,
                batch_label = excluded.batch_label,
                fetched_at = CURRENT_TIMESTAMP,
                analyzed_at = CURRENT_TIMESTAMP
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
                item.get("source_type"),
                item.get("source_trust_level"),
                item.get("language"),
                batch_label,
            ),
        )

        if existing:
            duplicates += 1
        else:
            inserted += 1

    return inserted, duplicates


def store_trending_topics(cursor, topics: list[dict]):
    cursor.execute("DELETE FROM trending_topics")
    for topic in topics:
        cursor.execute(
            """
            INSERT INTO trending_topics (
                topic, region, intensity, article_count, freshness, credibility_warning, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                topic["topic"],
                topic["region"],
                topic["intensity"],
                topic["article_count"],
                topic["freshness"],
                1 if topic["credibility_warning"] else 0,
            ),
        )


def save_refresh_log(
    cursor,
    batch_label: str,
    started_at: str,
    finished_at: str,
    inserted_count: int,
    duplicate_count: int,
    failed_source_count: int,
    trend_update_count: int,
):
    cursor.execute(
        """
        INSERT INTO refresh_logs (
            batch_label, started_at, finished_at, inserted_count,
            duplicate_count, failed_source_count, trend_update_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            batch_label,
            started_at,
            finished_at,
            inserted_count,
            duplicate_count,
            failed_source_count,
            trend_update_count,
        ),
    )


def get_news_from_db(country: Optional[str] = None, category: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM news_articles WHERE 1=1"
    params = []

    if country:
        query += " AND lower(country) = lower(?)"
        params.append(country)

    if category and category != "All":
        query += " AND lower(category) = lower(?)"
        params.append(category)

    query += " ORDER BY published_at DESC LIMIT 100"

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
    return [row["category"] for row in rows if row["category"]]


def get_trending_topics(region: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT topic, region, intensity, article_count, freshness, credibility_warning FROM trending_topics"
    params = []

    if region:
        query += " WHERE lower(region) = lower(?)"
        params.append(region)

    query += " ORDER BY intensity DESC, article_count DESC LIMIT 12"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        item = dict(row)
        item["credibility_warning"] = bool(item["credibility_warning"])
        results.append(item)
    return results


def get_overview_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS count FROM news_articles")
    total_articles = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) AS count FROM news_articles WHERE country = 'ma'")
    morocco_articles = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) AS count FROM news_articles WHERE country = 'world'")
    world_articles = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) AS count FROM news_articles WHERE credibility_label = 'Reliable'")
    reliable_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) AS count FROM news_articles WHERE credibility_label IN ('Suspicious', 'High Risk')")
    suspicious_count = cursor.fetchone()["count"]

    cursor.execute("""
        SELECT batch_label, finished_at
        FROM refresh_logs
        ORDER BY id DESC
        LIMIT 1
    """)
    latest = cursor.fetchone()
    conn.close()

    return {
        "total_articles": total_articles,
        "morocco_articles": morocco_articles,
        "world_articles": world_articles,
        "reliable_count": reliable_count,
        "suspicious_count": suspicious_count,
        "last_refresh_batch": latest["batch_label"] if latest else None,
        "last_refresh_at": latest["finished_at"] if latest else None,
    }


def get_refresh_logs(limit: int = 10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT batch_label, started_at, finished_at, inserted_count,
               duplicate_count, failed_source_count, trend_update_count
        FROM refresh_logs
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


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
        json.dumps(result["risk_signals"]),
    ))

    conn.commit()
    conn.close()


def get_recent_user_checks(limit: int = 6):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT input_type, input_value, credibility_label, credibility_score, created_at
        FROM user_checks
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


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