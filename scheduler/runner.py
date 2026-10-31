"""APScheduler daily job runner at 10:00 AM PKT with retries and error notifications."""
import asyncio
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config.settings import settings
from config.profile_loader import load_profile
from pipeline.news_pipeline import NewsPipeline
from jobs.pipeline import JobsPipeline
from jobs.store.job_repo import JobRepository
from database.news_repo import NewsRepository
from database.connection import db_session
from mailer.renderer import DigestRenderer
from mailer.sender import EmailSender

logger = logging.getLogger(__name__)


def record_digest_run(status: str, news_count: int, jobs_count: int, subject: str = None, error_msg: str = None):
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO digest_runs (run_time, status, news_count, jobs_count, subject, recipient_list, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            status,
            news_count,
            jobs_count,
            subject,
            ", ".join(settings.recipient_list),
            error_msg
        ))


async def run_daily_briefing(max_retries: int = 3) -> bool:
    """Run full briefing pipeline: fetch news, fetch jobs, render digest, send email."""
    logger.info("Starting Daily Briefing execution...")
    renderer = DigestRenderer()
    sender = EmailSender()

    attempt = 0
    last_error: Exception = None

    while attempt < max_retries:
        attempt += 1
        logger.info(f"Pipeline execution attempt {attempt} of {max_retries}...")
        try:
            profile = load_profile()

            # 1. News Pipeline
            news_pipeline = NewsPipeline(profile=profile)
            news_items = await news_pipeline.run(top_limit=20)

            # 2. Jobs Pipeline
            jobs_pipeline = JobsPipeline(profile=profile)
            saved_jobs = await jobs_pipeline.run()

            # 3. Pull closing soon and read later from database
            closing_soon = JobRepository.get_closing_soon_jobs(days_window=5)
            read_later = NewsRepository.get_history(only_read_later=True, limit=5)

            # 4. Render email in rich Urdu
            subject, html_body, txt_body = renderer.render_urdu_digest(
                news_items=news_items,
                jobs=saved_jobs,
                closing_soon=closing_soon
            )

            # 5. Dispatch email
            success = sender.send_email(subject, html_body, txt_body)

            # 6. Record run log
            record_digest_run(
                status="success" if success else "failed",
                news_count=len(news_items),
                jobs_count=len(saved_jobs),
                subject=subject,
                error_msg=None if success else "Email dispatch returned false"
            )

            logger.info("Daily Briefing finished successfully!")
            return True

        except Exception as ex:
            last_error = ex
            logger.error(f"Attempt {attempt} failed with error: {ex}")
            if attempt < max_retries:
                await asyncio.sleep(2 * attempt)  # Backoff before retry

    # All 3 retries failed -> send error notification email!
    error_str = f"Pipeline failed after {max_retries} attempts. Error: {str(last_error)}"
    logger.critical(error_str)
    record_digest_run(status="failed", news_count=0, jobs_count=0, error_msg=error_str)

    try:
        err_subj, err_html = renderer.render_error_alert(error_str)
        sender.send_email(err_subj, err_html, text_content=error_str)
    except Exception as notify_err:
        logger.error(f"Failed sending error notification: {notify_err}")

    return False


scheduler: AsyncIOScheduler = None


def start_scheduler():
    """Start APScheduler daily at 10:00 AM in configured timezone."""
    global scheduler
    if scheduler and scheduler.running:
        return scheduler

    tz_str = settings.TIMEZONE or "Asia/Karachi"
    try:
        tz = ZoneInfo(tz_str)
    except Exception:
        tz = ZoneInfo("Asia/Karachi")

    # Parse DIGEST_TIME (e.g. "10:00")
    try:
        parts = settings.DIGEST_TIME.split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
    except Exception:
        hour, minute = 10, 0

    scheduler = AsyncIOScheduler(timezone=tz)
    scheduler.add_job(
        run_daily_briefing,
        trigger=CronTrigger(hour=hour, minute=minute, timezone=tz),
        id="daily_devresearch_briefing",
        name=f"Daily Briefing at {hour:02d}:{minute:02d} ({tz_str})",
        replace_existing=True
    )
    scheduler.start()
    logger.info(f"APScheduler scheduled daily briefing at {hour:02d}:{minute:02d} in {tz_str}")
    return scheduler
