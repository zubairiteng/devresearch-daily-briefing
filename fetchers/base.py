"""Base fetcher interface and raw item model."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class RawItem:
    title: str
    url: str
    source_name: str
    category: str = "ai_llm"  # "ai_llm", "software_cloud", "research_watch"
    content: str = ""
    summary: str = ""
    published_at: Optional[datetime] = None
    author: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def clean_title(self) -> str:
        return " ".join(self.title.strip().split())


class BaseFetcher:
    """Abstract base class for all content fetchers."""
    name: str = "BaseFetcher"

    async def fetch(self) -> List[RawItem]:
        raise NotImplementedError
