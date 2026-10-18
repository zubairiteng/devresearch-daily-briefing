"""Base job fetcher and raw job data structure."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class RawJob:
    title: str
    organization: str
    city: str
    url: str
    source_name: str
    description: str = ""
    raw_qualification: Optional[str] = None
    raw_experience: Optional[str] = None
    raw_age_limit: Optional[str] = None
    raw_salary: Optional[str] = None
    raw_deadline: Optional[str] = None
    apply_link: Optional[str] = None
    job_type: str = "Full-Time"  # "Permanent", "Contract", "Visiting", "Full-Time"
    fetched_at: Optional[datetime] = None
    extra_sources: List[str] = field(default_factory=list)


class BaseJobFetcher:
    name: str = "BaseJobFetcher"

    async def fetch(self) -> List[RawJob]:
        raise NotImplementedError
