from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from app.database import refresh_news_batch


def get_batch_label():
    hour = datetime.now().hour

    if 6 <= hour < 12:
        return "morning_brief"
    elif 12 <= hour < 18:
        return "midday_update"
    return "evening_recap"


def refresh_news():
    batch_label = get_batch_label()
    count = refresh_news_batch(batch_label)
    print(f"[TruthLens Scheduler] refresh_news executed with batch: {batch_label} ({count} items)")


def start_scheduler():
    scheduler = BackgroundScheduler()

    scheduler.add_job(refresh_news, "cron", hour=6, minute=0, id="morning_job")
    scheduler.add_job(refresh_news, "cron", hour=12, minute=0, id="midday_job")
    scheduler.add_job(refresh_news, "cron", hour=18, minute=0, id="evening_job")

    scheduler.start()
    print("[TruthLens Scheduler] APScheduler started")
    return scheduler
