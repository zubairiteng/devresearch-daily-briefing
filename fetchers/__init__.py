"""Content fetchers module."""
from .base import BaseFetcher, RawItem
from .rss_fetcher import RSSFetcher
from .arxiv_fetcher import ArxivFetcher
from .hn_fetcher import HackerNewsFetcher
from .reddit_fetcher import RedditFetcher
from .github_fetcher import GitHubFetcher
from .podcast_fetcher import PodcastFetcher

__all__ = [
    "BaseFetcher",
    "RawItem",
    "RSSFetcher",
    "ArxivFetcher",
    "HackerNewsFetcher",
    "RedditFetcher",
    "GitHubFetcher",
    "PodcastFetcher",
]
