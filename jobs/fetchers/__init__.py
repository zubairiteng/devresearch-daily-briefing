"""Job fetchers package."""
from .base_job_fetcher import BaseJobFetcher, RawJob
from .indeed_fetcher import IndeedPKFetcher
from .university_fetcher import UniversityJobFetcher
from .govt_skills_fetcher import GovtSkillsJobFetcher
from .imap_fetcher import ImapJobAlertFetcher
from .remote_fetcher import RemoteAIJobFetcher, detect_pakistan_eligibility

__all__ = [
    "BaseJobFetcher",
    "RawJob",
    "IndeedPKFetcher",
    "UniversityJobFetcher",
    "GovtSkillsJobFetcher",
    "ImapJobAlertFetcher",
    "RemoteAIJobFetcher",
    "detect_pakistan_eligibility",
]

