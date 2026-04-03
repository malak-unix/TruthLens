from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from app.database import get_connection
from app.mock_news import mock_news


def get_batch_label():
    hour = datetime.now().hour

    if 6 <= hour < 12:
        return "morning_brief"
    elif 12 <= hour < 18:
        return "midday_update"
    return "evening_recap"


def refresh_news():
    conn = get_connection()
    cursor = conn.cursor()
    batch_label = get_batch_label()

    for item in mock_news:
        cursor.execute("""
        INSERT OR REPLACE INTO news_articles (
            id, title, source_name, published_at, country, category, url,
            description, credibility_score, credibility_label, explanation, batch_label, fetched_at
        )
        VALUES (
            (SELECT id FROM news_articles WHERE url = ?),
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP
        )
        """, (
            item["url"],
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
            batch_label
        ))

    conn.commit()
    conn.close()
    print(f"[TruthLens Scheduler] refresh_news executed with batch: {batch_label}")


def start_scheduler():
    scheduler = BackgroundScheduler()

    scheduler.add_job(refresh_news, "cron", hour=6, minute=0, id="morning_job")
    scheduler.add_job(refresh_news, "cron", hour=12, minute=0, id="midday_job")
    scheduler.add_job(refresh_news, "cron", hour=18, minute=0, id="evening_job")

    scheduler.start()
    print("[TruthLens Scheduler] APScheduler started")
    return scheduler