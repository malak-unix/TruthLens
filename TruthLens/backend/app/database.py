import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "truthlens.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_column(cursor, table: str, column: str, definition: str):
    cursor.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cursor.fetchall()}
    if column not in existing:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
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
        """
    )

    cursor.execute(
        """
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
        """
    )

    cursor.execute(
        """
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
        """
    )

    cursor.execute(
        """
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
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    _ensure_column(cursor, "news_articles", "provider_name", "TEXT")
    _ensure_column(cursor, "news_articles", "source_domain", "TEXT")
    _ensure_column(cursor, "news_articles", "image_url", "TEXT")
    _ensure_column(cursor, "news_articles", "priority_topic", "TEXT")
    _ensure_column(cursor, "news_articles", "priority_score", "REAL DEFAULT 0")
    _ensure_column(cursor, "news_articles", "trend_score", "REAL DEFAULT 0")
    _ensure_column(cursor, "news_articles", "coverage_score", "REAL DEFAULT 0")
    _ensure_column(cursor, "news_articles", "ranking_score", "REAL DEFAULT 0")
    _ensure_column(cursor, "news_articles", "dedupe_key", "TEXT")
    _ensure_column(cursor, "news_articles", "is_priority", "INTEGER DEFAULT 0")
    _ensure_column(cursor, "news_articles", "is_conflict", "INTEGER DEFAULT 0")
    _ensure_column(cursor, "news_articles", "completeness_score", "REAL DEFAULT 0")
    _ensure_column(cursor, "news_articles", "source_score", "INTEGER")
    _ensure_column(cursor, "news_articles", "article_score", "INTEGER")
    _ensure_column(cursor, "news_articles", "corroboration_score", "INTEGER")
    _ensure_column(cursor, "news_articles", "verification_status", "TEXT")
    _ensure_column(cursor, "trending_topics", "title", "TEXT")
    _ensure_column(cursor, "trending_topics", "normalized_topic", "TEXT")
    _ensure_column(cursor, "trending_topics", "source_signals", "TEXT DEFAULT '[]'")
    _ensure_column(cursor, "trending_topics", "platform_signals", "TEXT DEFAULT '[]'")
    _ensure_column(cursor, "trending_topics", "related_articles_count", "INTEGER DEFAULT 0")
    _ensure_column(cursor, "trending_topics", "recency_score", "REAL DEFAULT 0")
    _ensure_column(cursor, "trending_topics", "virality_score", "REAL DEFAULT 0")
    _ensure_column(cursor, "trending_topics", "verification_score", "REAL DEFAULT 0")
    _ensure_column(cursor, "trending_topics", "verification_gap_score", "REAL DEFAULT 0")
    _ensure_column(cursor, "trending_topics", "freshness_label", "TEXT DEFAULT 'active'")
    _ensure_column(cursor, "trending_topics", "confidence_note", "TEXT DEFAULT ''")
    _ensure_column(cursor, "trending_topics", "platform", "TEXT DEFAULT 'news'")
    _ensure_column(cursor, "trending_topics", "media_type", "TEXT DEFAULT 'text'")
    _ensure_column(cursor, "trending_topics", "thumbnail_url", "TEXT DEFAULT ''")
    _ensure_column(cursor, "trending_topics", "source_url", "TEXT DEFAULT ''")
    _ensure_column(cursor, "trending_topics", "verification_status", "TEXT DEFAULT 'unverified'")

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_news_articles_region_rank
        ON news_articles(country, ranking_score DESC, published_at DESC)
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_news_articles_category_rank
        ON news_articles(category, ranking_score DESC, published_at DESC)
        """
    )

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
                image_url, description, credibility_score, credibility_label, explanation,
                source_type, source_trust_level, language, batch_label, fetched_at, analyzed_at,
                provider_name, source_domain, priority_topic, priority_score, trend_score,
                coverage_score, ranking_score, dedupe_key, is_priority, is_conflict, completeness_score,
                source_score, article_score, corroboration_score, verification_status
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            ON CONFLICT(url) DO UPDATE SET
                title = excluded.title,
                source_name = excluded.source_name,
                published_at = excluded.published_at,
                country = excluded.country,
                category = excluded.category,
                image_url = excluded.image_url,
                description = excluded.description,
                credibility_score = excluded.credibility_score,
                credibility_label = excluded.credibility_label,
                explanation = excluded.explanation,
                source_type = excluded.source_type,
                source_trust_level = excluded.source_trust_level,
                language = excluded.language,
                batch_label = excluded.batch_label,
                fetched_at = CURRENT_TIMESTAMP,
                analyzed_at = CURRENT_TIMESTAMP,
                provider_name = excluded.provider_name,
                source_domain = excluded.source_domain,
                priority_topic = excluded.priority_topic,
                priority_score = excluded.priority_score,
                trend_score = excluded.trend_score,
                coverage_score = excluded.coverage_score,
                ranking_score = excluded.ranking_score,
                dedupe_key = excluded.dedupe_key,
                is_priority = excluded.is_priority,
                is_conflict = excluded.is_conflict,
                completeness_score = excluded.completeness_score,
                source_score = excluded.source_score,
                article_score = excluded.article_score,
                corroboration_score = excluded.corroboration_score,
                verification_status = excluded.verification_status
            """,
            (
                item["title"],
                item["source_name"],
                item["published_at"],
                item["country"],
                item["category"],
                item["url"],
                item.get("image_url"),
                item["description"],
                item["credibility_score"],
                item["credibility_label"],
                item["explanation"],
                item.get("source_type"),
                item.get("source_trust_level"),
                item.get("language"),
                batch_label,
                item.get("provider_name"),
                item.get("source_domain"),
                item.get("priority_topic"),
                item.get("priority_score", 0),
                item.get("trend_score", 0),
                item.get("coverage_score", 0),
                item.get("ranking_score", 0),
                item.get("dedupe_key", ""),
                1 if item.get("is_priority") else 0,
                1 if item.get("is_conflict") else 0,
                item.get("completeness_score", 0),
                item.get("source_score"),
                item.get("article_score"),
                item.get("corroboration_score"),
                item.get("verification_status"),
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
                topic, title, normalized_topic, region, intensity, article_count, freshness,
                credibility_warning, source_signals, platform_signals, related_articles_count,
                recency_score, virality_score, verification_score, verification_gap_score,
                freshness_label, confidence_note, platform, media_type, thumbnail_url,
                source_url, verification_status, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                topic["topic"],
                topic.get("title", topic["topic"]),
                topic.get("normalized_topic", ""),
                topic["region"],
                topic["intensity"],
                topic["article_count"],
                topic["freshness"],
                1 if topic["credibility_warning"] else 0,
                topic.get("source_signals", "[]"),
                topic.get("platform_signals", "[]"),
                topic.get("related_articles_count", topic["article_count"]),
                topic.get("recency_score", 0),
                topic.get("virality_score", 0),
                topic.get("verification_score", 0),
                topic.get("verification_gap_score", 0),
                topic.get("freshness_label", topic["freshness"]),
                topic.get("confidence_note", ""),
                topic.get("platform", "news"),
                topic.get("media_type", "text"),
                topic.get("thumbnail_url", ""),
                topic.get("source_url", ""),
                topic.get("verification_status", "unverified"),
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


def prune_old_news(cursor, retention_days: int) -> int:
    if retention_days <= 0:
        return 0

    cursor.execute(
        """
        DELETE FROM news_articles
        WHERE datetime(fetched_at) < datetime('now', ?)
        """,
        (f"-{retention_days} days",),
    )
    return cursor.rowcount or 0


def _hydrate_news_rows(conn, cursor, rows):
    results = []
    needs_commit = False

    for row in rows:
        item = dict(row)

        if (
            item.get("source_score") is None
            or item.get("article_score") is None
            or item.get("corroboration_score") is None
            or not item.get("verification_status")
        ):
            from app.analyzer import analyze_payload

            analysis = analyze_payload(
                text=f"{item.get('title', '')}. {item.get('description', '')}",
                url=item.get("url", ""),
                source_name=item.get("source_name", ""),
                article_metadata={
                    "url": item.get("url", ""),
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "text": item.get("description", ""),
                    "published_at": item.get("published_at", ""),
                    "author": "",
                },
            )

            item["source_score"] = analysis.get("source_score")
            item["article_score"] = analysis.get("article_score")
            item["corroboration_score"] = analysis.get("corroboration_score")
            item["verification_status"] = analysis.get("verification_status")
            item["credibility_score"] = analysis.get("credibility_score", item.get("credibility_score"))
            item["credibility_label"] = analysis.get("credibility_label", item.get("credibility_label"))
            item["explanation"] = analysis.get("explanation", item.get("explanation"))

            cursor.execute(
                """
                UPDATE news_articles
                SET source_score = ?, article_score = ?, corroboration_score = ?,
                    verification_status = ?, credibility_score = ?, credibility_label = ?,
                    explanation = ?, analyzed_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    item["source_score"],
                    item["article_score"],
                    item["corroboration_score"],
                    item["verification_status"],
                    item["credibility_score"],
                    item["credibility_label"],
                    item["explanation"],
                    item["id"],
                ),
            )
            needs_commit = True

        item["is_priority"] = bool(item.get("is_priority"))
        item["is_conflict"] = bool(item.get("is_conflict"))
        results.append(item)

    if needs_commit:
        conn.commit()

    return results


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

    query += " ORDER BY ranking_score DESC, published_at DESC LIMIT 100"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = _hydrate_news_rows(conn, cursor, rows)

    conn.close()
    return results


def get_historical_news_from_db(
    country: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 60,
):
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

    if search:
        query += """
            AND (
                lower(title) LIKE lower(?)
                OR lower(description) LIKE lower(?)
                OR lower(source_name) LIKE lower(?)
                OR lower(url) LIKE lower(?)
            )
        """
        needle = f"%{search}%"
        params.extend([needle, needle, needle, needle])

    safe_limit = max(10, min(limit, 200))
    query += " ORDER BY datetime(analyzed_at) DESC, datetime(fetched_at) DESC, datetime(published_at) DESC LIMIT ?"
    params.append(safe_limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = _hydrate_news_rows(conn, cursor, rows)

    conn.close()
    return results


def get_recent_articles_for_corroboration(limit: int = 80):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT title, description, source_name, source_domain, source_trust_level, published_at,
               credibility_score, credibility_label, country
        FROM news_articles
        ORDER BY published_at DESC, id DESC
        LIMIT ?
        """,
        (limit,),
    )
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

    query = """
        SELECT topic, title, normalized_topic, region, intensity, article_count, freshness,
               credibility_warning, source_signals, platform_signals, related_articles_count,
               recency_score, virality_score, verification_score, verification_gap_score,
               freshness_label, confidence_note, platform, media_type, thumbnail_url,
               source_url, verification_status
        FROM trending_topics
    """
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
        item["source_signals"] = json.loads(item.get("source_signals") or "[]")
        item["platform_signals"] = json.loads(item.get("platform_signals") or "[]")
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

    cursor.execute(
        "SELECT COUNT(*) AS count FROM news_articles WHERE credibility_label IN ('Suspicious', 'High Risk')"
    )
    suspicious_count = cursor.fetchone()["count"]

    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM user_checks
        WHERE datetime(created_at) >= datetime('now', 'start of day')
        """
    )
    checks_today = cursor.fetchone()["count"]

    cursor.execute(
        """
        SELECT batch_label, finished_at
        FROM refresh_logs
        ORDER BY id DESC
        LIMIT 1
        """
    )
    latest = cursor.fetchone()
    conn.close()

    return {
        "total_articles": total_articles,
        "morocco_articles": morocco_articles,
        "world_articles": world_articles,
        "reliable_count": reliable_count,
        "suspicious_count": suspicious_count,
        "checks_today": checks_today,
        "last_refresh_batch": latest["batch_label"] if latest else None,
        "last_refresh_at": latest["finished_at"] if latest else None,
    }


def get_refresh_logs(limit: int = 10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT batch_label, started_at, finished_at, inserted_count,
               duplicate_count, failed_source_count, trend_update_count
        FROM refresh_logs
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def save_user_check(input_type: str, input_value: str, result: dict):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO user_checks (
            input_type, input_value, credibility_score,
            credibility_label, explanation, risk_signals
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            input_type,
            input_value,
            result["credibility_score"],
            result["credibility_label"],
            result["explanation"],
            json.dumps(result["risk_signals"]),
        ),
    )

    conn.commit()
    conn.close()


def get_recent_user_checks(limit: int = 6):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT input_type, input_value, credibility_label, credibility_score, created_at
        FROM user_checks
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def create_user(full_name: str, email: str, password_hash: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users (full_name, email, password_hash)
        VALUES (?, ?, ?)
        """,
        (full_name, email.lower(), password_hash),
    )
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


def needs_refresh(max_age_minutes: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT finished_at
        FROM refresh_logs
        ORDER BY id DESC
        LIMIT 1
        """
    )
    row = cursor.fetchone()
    conn.close()

    if not row or not row["finished_at"]:
        return True

    try:
        finished_at = datetime.fromisoformat(row["finished_at"].replace("Z", "+00:00"))
    except ValueError:
        return True

    age_minutes = (datetime.now(timezone.utc) - finished_at.astimezone(timezone.utc)).total_seconds() / 60
    return age_minutes >= max_age_minutes
