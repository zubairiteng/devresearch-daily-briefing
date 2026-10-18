"""Hacker News API fetcher filtered by AI, cloud, and dev topics."""
import asyncio
import logging
from datetime import datetime, timezone
from typing import List
import httpx

from .base import BaseFetcher, RawItem
from config.sources_loader import HackerNewsConfig

logger = logging.getLogger(__name__)


class HackerNewsFetcher(BaseFetcher):
    name = "HackerNewsFetcher"

    def __init__(self, config: HackerNewsConfig):
        self.config = config

    async def fetch(self) -> List[RawItem]:
        if not self.config.enabled:
            return []

        items: List[RawItem] = []
        async with httpx.AsyncClient(timeout=12.0) as client:
            try:
                top_resp = await client.get(f"{self.config.api_url}/topstories.json")
                if top_resp.status_code != 200:
                    return []
                story_ids = top_resp.json()[:self.config.max_items]

                # Fetch story details concurrently in chunks
                chunk_size = 10
                for i in range(0, len(story_ids), chunk_size):
                    chunk = story_ids[i:i + chunk_size]
                    tasks = [client.get(f"{self.config.api_url}/item/{sid}.json") for sid in chunk]
                    responses = await asyncio.gather(*tasks, return_exceptions=True)

                    for resp in responses:
                        if isinstance(resp, Exception) or resp.status_code != 200:
                            continue
                        data = resp.json()
                        if not data or data.get("type") != "story":
                            continue

                        title = data.get("title", "").strip()
                        url = data.get("url", f"https://news.ycombinator.com/item?id={data.get('id')}")
                        score = data.get("score", 0)

                        # Filter by relevant keywords
                        title_lower = title.lower()
                        matches = any(kw.lower() in title_lower for kw in self.config.keywords_filter)
                        if not matches:
                            continue

                        # Classify category
                        category = "software_cloud"
                        if any(k in title_lower for k in ["llm", "gpt", "claude", "gemini", "deepseek", "ai", "model", "prompt"]):
                            category = "ai_llm"
                        elif any(k in title_lower for k in ["paper", "quantum", "arxiv", "research", "benchmark"]):
                            category = "research_watch"

                        items.append(
                            RawItem(
                                title=title,
                                url=url,
                                source_name="Hacker News",
                                category=category,
                                content=f"Hacker News discussion ({score} points). {title}",
                                summary=f"Popular community discussion on Hacker News ({score} points): {title}",
                                published_at=datetime.fromtimestamp(data.get("time", 0), timezone.utc),
                                author=data.get("by"),
                                extra={"score": score, "hn_id": data.get("id")}
                            )
                        )
                logger.info(f"Fetched {len(items)} filtered stories from Hacker News")
            except Exception as e:
                logger.error(f"Error fetching from Hacker News: {e}")
        return items
