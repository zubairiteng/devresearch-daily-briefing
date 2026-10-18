"""Podcast feed fetcher for AI leader interviews and quotes."""
import logging
from datetime import datetime, timezone
from typing import List
import feedparser
import httpx
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from .base import BaseFetcher, RawItem
from config.sources_loader import PodcastConfig

logger = logging.getLogger(__name__)


def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    return " ".join(soup.get_text(separator=" ", strip=True).split())


class PodcastFetcher(BaseFetcher):
    name = "PodcastFetcher"

    def __init__(self, config: PodcastConfig):
        self.config = config

    async def fetch(self) -> List[RawItem]:
        if not self.config.enabled:
            return []

        items: List[RawItem] = []
        async with httpx.AsyncClient(timeout=15.0, headers={"User-Agent": "DevResearchBriefing/1.0"}) as client:
            for feed in self.config.feeds:
                try:
                    resp = await client.get(feed.url)
                    if resp.status_code != 200:
                        continue
                    parsed = feedparser.parse(resp.text)

                    # Get latest 2 episodes
                    for entry in parsed.entries[:2]:
                        title = entry.get("title", "").strip()
                        link = entry.get("link", "").strip()
                        raw_desc = entry.get("summary") or entry.get("description") or ""
                        cleaned_desc = clean_html(raw_desc)[:800]

                        pub_str = entry.get("published", "")
                        pub_date = None
                        if pub_str:
                            try:
                                pub_date = date_parser.parse(pub_str)
                                if pub_date.tzinfo is None:
                                    pub_date = pub_date.replace(tzinfo=timezone.utc)
                            except Exception:
                                pass

                        items.append(
                            RawItem(
                                title=f"Podcast Takeaway: {title}",
                                url=link,
                                source_name=feed.name,
                                category="ai_llm",
                                content=cleaned_desc,
                                summary=f"Interview insights from {feed.name} ({feed.speaker_hint or 'Host & Guest'}): {cleaned_desc[:300]}",
                                published_at=pub_date or datetime.now(timezone.utc),
                                author=feed.speaker_hint,
                                extra={"is_podcast": True, "show": feed.name}
                            )
                        )
                except Exception as e:
                    logger.warning(f"Error fetching podcast {feed.name}: {e}")
        return items
