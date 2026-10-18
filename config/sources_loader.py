"""Sources configuration loader for news, research, and Pakistani jobs."""
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCES_PATH = BASE_DIR / "sources.yaml"


class RSSFeedConfig(BaseModel):
    name: str
    category: str
    url: str
    enabled: bool = True
    rss_alternative: Optional[str] = None


class ArxivConfig(BaseModel):
    enabled: bool = True
    api_url: str = "https://export.arxiv.org/api/query"
    categories: List[str] = Field(default_factory=lambda: ["cs.CL", "cs.AI", "cs.LG", "quant-ph"])
    max_results: int = 15
    sort_by: str = "submittedDate"
    sort_order: str = "descending"


class HackerNewsConfig(BaseModel):
    enabled: bool = True
    api_url: str = "https://hacker-news.firebaseio.com/v0"
    max_items: int = 30
    keywords_filter: List[str] = Field(default_factory=list)


class RedditSubreddit(BaseModel):
    name: str
    url: str
    category: str


class RedditConfig(BaseModel):
    enabled: bool = True
    subreddits: List[RedditSubreddit] = Field(default_factory=list)


class GitHubConfig(BaseModel):
    enabled: bool = True
    repositories: List[str] = Field(default_factory=list)


class PodcastFeed(BaseModel):
    name: str
    url: str
    speaker_hint: Optional[str] = None


class PodcastConfig(BaseModel):
    enabled: bool = True
    feeds: List[PodcastFeed] = Field(default_factory=list)


class NewsSources(BaseModel):
    rss_feeds: List[RSSFeedConfig] = Field(default_factory=list)
    arxiv: ArxivConfig = Field(default_factory=ArxivConfig)
    hacker_news: HackerNewsConfig = Field(default_factory=HackerNewsConfig)
    reddit: RedditConfig = Field(default_factory=RedditConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    podcasts: PodcastConfig = Field(default_factory=PodcastConfig)


class JobSourceConfig(BaseModel):
    name: str
    type: str  # "rss", "university_portal", "govt_portal", "skills_portal", "portal_search"
    url: str
    city: str = "Lahore"
    manual_url: Optional[str] = None
    enabled: bool = True


class ImapAlertConfig(BaseModel):
    enabled: bool = False
    folder: str = "INBOX"
    filter_subjects: List[str] = Field(default_factory=list)


class JobSources(BaseModel):
    pakistan_sources: List[JobSourceConfig] = Field(default_factory=list)
    imap_email_alerts: ImapAlertConfig = Field(default_factory=ImapAlertConfig)
    remote_sources: List[Dict[str, Any]] = Field(default_factory=list)


class AppSources(BaseModel):
    news: NewsSources = Field(default_factory=NewsSources)
    jobs: JobSources = Field(default_factory=JobSources)


def load_sources(path: Optional[Path] = None) -> AppSources:
    file_path = path or SOURCES_PATH
    if not file_path.exists():
        return AppSources()
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return AppSources(**data)


def save_sources(sources_dict: Dict[str, Any], path: Optional[Path] = None) -> None:
    file_path = path or SOURCES_PATH
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(sources_dict, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
