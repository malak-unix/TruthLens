from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from app.ingestion_service import run_ingestion_pipeline


def get_batch_label():
    hour = datetime.now().hour
    if 6 <= hour < 12:
        return "morning_refresh"
    if 12 <= hour < 18:
        return "midday_refresh"
    return "evening_refresh"


def refresh_news():
    batch_label = get_batch_label()
    result = run_ingestion_pipeline(batch_label)
    print(f"[TruthLens Scheduler] {result}")


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(refresh_news, "cron", hour=6, minute=0, id="morning_job")
    scheduler.add_job(refresh_news, "cron", hour=12, minute=0, id="midday_job")
    scheduler.add_job(refresh_news, "cron", hour=18, minute=0, id="evening_job")
    scheduler.start()
    print("[TruthLens Scheduler] APScheduler started")
    return scheduler