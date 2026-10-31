"""Standalone CLI runner for DevResearch Daily Briefing.

Used by GitHub Actions, system cron, and local manual executions.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("devresearch.cli")

from database.connection import init_db
from database.news_repo import NewsRepository
from jobs.store.job_repo import JobRepository
from scheduler.runner import run_daily_briefing
from mailer.renderer import DigestRenderer


async def main():
    logger.info("Initializing DevResearch Database...")
    init_db()

    logger.info("Executing Daily Briefing Pipeline with live fetchers...")
    success = await run_daily_briefing(max_retries=3)

    if not success:
        logger.error("Daily briefing failed.")
        sys.exit(1)

    # Export sample_digest.html using real data from the database
    renderer = DigestRenderer()
    news_items = NewsRepository.get_latest_news(limit=20)
    jobs = JobRepository.get_jobs(include_not_eligible=False, limit=10)
    closing_soon = JobRepository.get_closing_soon_jobs(days_window=5)
    read_later = NewsRepository.get_history(only_read_later=True, limit=5)

    subject, html_body, txt_body = renderer.render_urdu_digest(
        news_items=news_items,
        jobs=jobs,
        closing_soon=closing_soon
    )

    sample_html_path = Path(__file__).resolve().parent / "sample_digest.html"
    with open(sample_html_path, "w", encoding="utf-8") as f:
        f.write(html_body)

    logger.info(f"Successfully generated '{sample_html_path}' with real data!")
    logger.info(f"Summary: {len(news_items)} news items, {len(jobs)} active jobs for you.")


if __name__ == "__main__":
    asyncio.run(main())
