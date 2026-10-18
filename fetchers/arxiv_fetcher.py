"""arXiv API fetcher for NLP, LLMs, AI, and Quantum Computing research."""
import logging
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import feedparser
import httpx
from dateutil import parser as date_parser

from .base import BaseFetcher, RawItem
from config.sources_loader import ArxivConfig

logger = logging.getLogger(__name__)
USER_AGENT = "DevResearchBriefing/1.0 (arXiv researcher)"


class ArxivFetcher(BaseFetcher):
    name = "ArxivFetcher"

    def __init__(self, config: ArxivConfig, hours_lookback: int = 72):
        self.config = config
        self.hours_lookback = hours_lookback

    async def fetch(self) -> List[RawItem]:
        if not self.config.enabled:
            return []

        items: List[RawItem] = []
        # Construct search query: cat:cs.CL OR cat:cs.AI OR cat:cs.LG OR cat:quant-ph
        cat_query = " OR ".join([f"cat:{cat}" for cat in self.config.categories])
        params = {
            "search_query": cat_query,
            "sortBy": self.config.sort_by,
            "sortOrder": self.config.sort_order,
            "max_results": self.config.max_results
        }
        query_string = urllib.parse.urlencode(params)
        url = f"{self.config.api_url}?{query_string}"

        async with httpx.AsyncClient(timeout=20.0, headers={"User-Agent": USER_AGENT}) as client:
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"arXiv API responded with status {resp.status_code}")
                    return []

                parsed = feedparser.parse(resp.text)
                now = datetime.now(timezone.utc)
                cutoff = now - timedelta(hours=self.hours_lookback)

                for entry in parsed.entries:
                    raw_title = entry.get("title", "").replace("\n", " ").strip()
                    title = " ".join(raw_title.split())
                    paper_url = entry.get("link", "").strip()
                    abstract = entry.get("summary", "").replace("\n", " ").strip()
                    abstract = " ".join(abstract.split())

                    # Primary category
                    primary_cat = ""
                    if "arxiv_primary_category" in entry:
                        primary_cat = entry.arxiv_primary_category.get("term", "")

                    # Published date
                    pub_str = entry.get("published", "")
                    pub_date: Optional[datetime] = None
                    if pub_str:
                        try:
                            parsed_dt = date_parser.parse(pub_str)
                            if parsed_dt.tzinfo is None:
                                parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
                            pub_date = parsed_dt
                        except Exception:
                            pass

                    # Determine subcategory tag
                    sub_tag = "Research"
                    if "quant-ph" in primary_cat:
                        sub_tag = "Quantum Computing"
                    elif "cs.CL" in primary_cat:
                        sub_tag = "NLP & LLMs"
                    elif "cs.AI" in primary_cat or "cs.LG" in primary_cat:
                        sub_tag = "AI/ML Techniques"

                    items.append(
                        RawItem(
                            title=title,
                            url=paper_url,
                            source_name="arXiv",
                            category="research_watch",
                            content=abstract,
                            summary=abstract[:600],
                            published_at=pub_date or now,
                            author=entry.get("author", "arXiv Researchers"),
                            extra={
                                "primary_category": primary_cat,
                                "research_topic": sub_tag,
                                "is_research_paper": True
                            }
                        )
                    )
                logger.info(f"Fetched {len(items)} papers from arXiv")
            except Exception as e:
                logger.error(f"Error fetching from arXiv: {e}")

        return items
