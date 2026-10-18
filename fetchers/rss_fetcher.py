"""RSS & Atom feed fetcher with robust error handling and HTML cleanup."""
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import feedparser
from bs4 import BeautifulSoup
import httpx
from dateutil import parser as date_parser

from .base import BaseFetcher, RawItem
from config.sources_loader import RSSFeedConfig

logger = logging.getLogger(__name__)

USER_AGENT = "DevResearchBriefing/1.0 (+https://github.com/devresearch/daily-briefing)"


def clean_html(raw_html: str) -> str:
    """Strip tags, scripts, and normalize whitespace."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    for script_or_style in soup(["script", "style", "noscript", "svg", "img"]):
        script_or_style.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return " ".join(text.split())


class RSSFetcher(BaseFetcher):
    name = "RSSFetcher"

    def __init__(self, feeds: List[RSSFeedConfig], hours_lookback: int = 48):
        self.feeds = [f for f in feeds if f.enabled]
        self.hours_lookback = hours_lookback

    async def fetch(self) -> List[RawItem]:
        items: List[RawItem] = []
        async with httpx.AsyncClient(timeout=15.0, headers={"User-Agent": USER_AGENT}, follow_redirects=True) as client:
            for feed in self.feeds:
                try:
                    feed_items = await self._fetch_feed(client, feed)
                    items.extend(feed_items)
                    logger.info(f"Fetched {len(feed_items)} items from {feed.name}")
                except Exception as e:
                    logger.warning(f"Error fetching RSS feed '{feed.name}' ({feed.url}): {e}")
        return items

    async def _fetch_feed(self, client: httpx.AsyncClient, feed: RSSFeedConfig) -> List[RawItem]:
        results: List[RawItem] = []
        try:
            resp = await client.get(feed.url)
            if resp.status_code != 200 and feed.rss_alternative:
                resp = await client.get(feed.rss_alternative)
            if resp.status_code != 200:
                logger.warning(f"Feed {feed.name} returned status {resp.status_code}")
                return results

            parsed = feedparser.parse(resp.text)
            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(hours=self.hours_lookback)

            for entry in parsed.entries[:25]:
                title = entry.get("title", "").strip()
                url = entry.get("link", "").strip()
                if not title or not url:
                    continue

                # Parse date
                pub_date: Optional[datetime] = None
                date_fields = ["published", "updated", "created", "pubDate"]
                for df in date_fields:
                    val = entry.get(df)
                    if val:
                        try:
                            parsed_dt = date_parser.parse(val)
                            if parsed_dt.tzinfo is None:
                                parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
                            pub_date = parsed_dt
                            break
                        except Exception:
                            pass

                # If within lookback or date missing, keep it
                if pub_date and pub_date < cutoff:
                    continue

                # Content/Summary
                raw_content = ""
                if "content" in entry and entry["content"]:
                    raw_content = entry["content"][0].get("value", "")
                elif "summary" in entry:
                    raw_content = entry.get("summary", "")
                elif "description" in entry:
                    raw_content = entry.get("description", "")

                cleaned_content = clean_html(raw_content)

                results.append(
                    RawItem(
                        title=title,
                        url=url,
                        source_name=feed.name,
                        category=feed.category,
                        content=cleaned_content[:2500],
                        summary=cleaned_content[:500],
                        published_at=pub_date or now,
                        author=entry.get("author", None),
                        extra={"feed_name": feed.name}
                    )
                )
        except Exception as ex:
            logger.error(f"Failed processing feed {feed.name}: {ex}")
        return results
