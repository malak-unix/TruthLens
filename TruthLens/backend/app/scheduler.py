from datetime import datetime
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import get_settings
from app.database import needs_refresh
from app.ingestion_service import run_ingestion_pipeline


logger = logging.getLogger("truthlens.scheduler")


def get_batch_label():
    hour = datetime.now().hour
    if 6 <= hour < 12:
        return "morning_refresh"
    if 12 <= hour < 18:
        return "midday_refresh"
    return "evening_refresh"


def refresh_news():
    result = run_ingestion_pipeline(get_batch_label())
    logger.info("[TruthLens Scheduler] %s", result)


def refresh_priority_watch():
    result = run_ingestion_pipeline("priority_watch")
    logger.info("[TruthLens Scheduler] %s", result)


def start_scheduler():
    settings = get_settings()
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        refresh_news,
        "interval",
        minutes=max(30, settings.refresh_interval_minutes),
        id="full_refresh_job",
        replace_existing=True,
    )
    scheduler.add_job(
        refresh_priority_watch,
        "interval",
        minutes=max(20, settings.refresh_interval_minutes // 2),
        id="priority_watch_job",
        replace_existing=True,
    )

    scheduler.start()

    if needs_refresh(settings.startup_refresh_max_age_minutes):
        scheduler.add_job(
            refresh_priority_watch,
            trigger="date",
            run_date=datetime.now(),
            id="startup_refresh_job",
            replace_existing=True,
        )
        logger.info("[TruthLens Scheduler] scheduled startup refresh because local feed was stale")

    logger.info("[TruthLens Scheduler] APScheduler started")
    return scheduler
