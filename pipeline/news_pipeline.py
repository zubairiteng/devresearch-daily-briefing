"""News and research processing pipeline."""
import asyncio
import logging
from typing import List, Tuple
from config import load_profile, load_sources, UserProfile, AppSources
from fetchers import (
    RawItem, RSSFetcher, ArxivFetcher, HackerNewsFetcher,
    RedditFetcher, GitHubFetcher, PodcastFetcher
)
from processors import deduplicate_news, classify_item, score_item_relevance, rank_and_filter_items
from summarizer import LLMSummarizer, SummaryResult
from database.news_repo import NewsRepository
from database.models import NewsItemModel

logger = logging.getLogger(__name__)


class NewsPipeline:
    def __init__(self, profile: UserProfile = None, sources: AppSources = None):
        self.profile = profile or load_profile()
        self.sources = sources or load_sources()
        self.summarizer = LLMSummarizer(self.profile)

    async def run(self, top_limit: int = 20) -> List[NewsItemModel]:
        logger.info("Starting DevResearch news & research pipeline...")

        # 1. Initialize fetchers
        fetchers = [
            RSSFetcher(self.sources.news.rss_feeds),
            ArxivFetcher(self.sources.news.arxiv),
            HackerNewsFetcher(self.sources.news.hacker_news),
            RedditFetcher(self.sources.news.reddit),
            GitHubFetcher(self.sources.news.github),
            PodcastFetcher(self.sources.news.podcasts)
        ]

        # 2. Fetch concurrently from all sources
        tasks = [f.fetch() for f in fetchers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        raw_items: List[RawItem] = []
        for res in results:
            if isinstance(res, list):
                raw_items.extend(res)
            elif isinstance(res, Exception):
                logger.error(f"Fetcher task encountered error: {res}")

        logger.info(f"Total raw items gathered from all sources: {len(raw_items)}")

        # 3. Deduplicate
        unique_items = deduplicate_news(raw_items, similarity_threshold=0.65)
        logger.info(f"Unique items after deduplication: {len(unique_items)}")

        # 4. Classify & Score
        scored_candidates: List[Tuple[RawItem, int, str]] = []
        for item in unique_items:
            category = classify_item(item)
            item.category = category
            score = score_item_relevance(item, self.profile)
            scored_candidates.append((item, score, category))

        # Sort descending by score
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        top_candidates = scored_candidates[:top_limit]
        logger.info(f"Selected top {len(top_candidates)} items for summarization and database storage.")

        # 5. Summarize and save
        saved_items: List[NewsItemModel] = []
        for item, score, category in top_candidates:
            try:
                summary_res = await self.summarizer.summarize(item, category)
                item_id = NewsRepository.save_news_item(item, summary_res, score, category)
                saved_items.append(
                    NewsItemModel(
                        id=item_id,
                        title=summary_res.headline or item.title,
                        url=item.url,
                        source_name=item.source_name,
                        category=category,
                        summary=summary_res.summary_text,
                        why_it_matters=summary_res.why_it_matters,
                        research_gap=summary_res.research_gap,
                        published_at=item.published_at.isoformat() if item.published_at else None,
                        fetched_at=item.published_at.isoformat() if item.published_at else "",
                        score=score
                    )
                )
            except Exception as e:
                logger.error(f"Error summarizing item {item.title}: {e}")

        logger.info(f"News pipeline completed. Saved {len(saved_items)} items to SQLite.")
        return saved_items
