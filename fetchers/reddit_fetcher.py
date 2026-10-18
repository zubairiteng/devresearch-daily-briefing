"""Reddit JSON fetcher for r/MachineLearning and r/LocalLLaMA."""
import logging
from datetime import datetime, timezone
from typing import List
import httpx

from .base import BaseFetcher, RawItem
from config.sources_loader import RedditConfig

logger = logging.getLogger(__name__)
REDDIT_USER_AGENT = "DevResearchBot/1.0 (dev research briefing aggregator)"


class RedditFetcher(BaseFetcher):
    name = "RedditFetcher"

    def __init__(self, config: RedditConfig):
        self.config = config

    async def fetch(self) -> List[RawItem]:
        if not self.config.enabled:
            return []

        items: List[RawItem] = []
        async with httpx.AsyncClient(timeout=12.0, headers={"User-Agent": REDDIT_USER_AGENT}) as client:
            for sub in self.config.subreddits:
                try:
                    resp = await client.get(sub.url)
                    if resp.status_code != 200:
                        logger.warning(f"Reddit {sub.name} returned status {resp.status_code}")
                        continue

                    data = resp.json()
                    children = data.get("data", {}).get("children", [])
                    for post in children:
                        pdata = post.get("data", {})
                        if pdata.get("stickied", False):
                            continue

                        title = pdata.get("title", "").strip()
                        selftext = pdata.get("selftext", "").strip()
                        url = pdata.get("url", "")
                        permalink = f"https://reddit.com{pdata.get('permalink')}"
                        score = pdata.get("score", 0)

                        if not url:
                            url = permalink

                        # Build informative summary snippet
                        snippet = selftext[:300] if selftext else title

                        items.append(
                            RawItem(
                                title=title,
                                url=permalink,
                                source_name=sub.name,
                                category=sub.category,
                                content=selftext[:2000] or title,
                                summary=f"Community insight from {sub.name} ({score} upvotes): {snippet}",
                                published_at=datetime.fromtimestamp(pdata.get("created_utc", 0), timezone.utc),
                                author=pdata.get("author"),
                                extra={"score": score, "subreddit": sub.name, "external_url": url}
                            )
                        )
                    logger.info(f"Fetched {len(children)} posts from {sub.name}")
                except Exception as e:
                    logger.warning(f"Failed fetching Reddit {sub.name}: {e}")
        return items
