"""Indeed Pakistan live RSS job fetcher for Lahore, Gujranwala, and Punjab."""
import logging
from datetime import datetime, timezone
from typing import List
import feedparser
import httpx
from bs4 import BeautifulSoup

from .base_job_fetcher import BaseJobFetcher, RawJob
from config.sources_loader import JobSourceConfig

logger = logging.getLogger(__name__)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"


def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    return " ".join(soup.get_text(separator=" ", strip=True).split())


class IndeedPKFetcher(BaseJobFetcher):
    name = "IndeedPKFetcher"

    def __init__(self, sources: List[JobSourceConfig]):
        self.sources = [s for s in sources if s.enabled and s.type == "rss"]

    async def fetch(self) -> List[RawJob]:
        jobs: List[RawJob] = []
        async with httpx.AsyncClient(timeout=15.0, headers={"User-Agent": USER_AGENT}, follow_redirects=True) as client:
            for src in self.sources:
                try:
                    resp = await client.get(src.url)
                    if resp.status_code != 200:
                        logger.warning(f"Indeed RSS {src.name} returned status {resp.status_code}")
                        continue

                    parsed = feedparser.parse(resp.text)
                    for entry in parsed.entries[:10]:
                        title = entry.get("title", "").strip()
                        url = entry.get("link", "").strip()
                        raw_summary = entry.get("summary") or entry.get("description") or ""
                        clean_desc = clean_html(raw_summary)

                        # Extract organization from source or title (Indeed often formats "Title - Company - Location")
                        org = entry.get("source", {}).get("title") or "Pakistani Employer"
                        if " - " in title:
                            parts = title.split(" - ")
                            if len(parts) >= 2:
                                clean_job_title = parts[0].strip()
                                org = parts[1].strip()
                            else:
                                clean_job_title = title
                        else:
                            clean_job_title = title

                        jobs.append(
                            RawJob(
                                title=clean_job_title,
                                organization=org,
                                city=src.city,
                                url=url,
                                source_name=f"Indeed PK ({src.city})",
                                description=clean_desc,
                                apply_link=url,
                                fetched_at=datetime.now(timezone.utc)
                            )
                        )
                    logger.info(f"Fetched {len(parsed.entries)} jobs from {src.name}")
                except Exception as e:
                    logger.warning(f"Failed fetching Indeed RSS {src.name}: {e}")
        return jobs
