"""Pydantic data models for DevResearch entities."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NewsItemModel(BaseModel):
    id: Optional[int] = None
    title: str
    url: str
    source_name: str
    category: str  # "ai_llm", "software_cloud", "research_watch"
    summary: str
    why_it_matters: Optional[str] = None
    research_gap: Optional[str] = None
    published_at: Optional[str] = None
    fetched_at: str
    score: int = 50
    read_later: bool = False
    metadata: Optional[Dict[str, Any]] = None


class JobItemModel(BaseModel):
    id: Optional[int] = None
    title: str
    organization: str
    city: str
    job_type: str = "Full-Time"  # "Permanent", "Contract", "Visiting", "Full-Time"
    required_qualification: Optional[str] = "Not mentioned"
    required_experience: Optional[str] = "Not mentioned"
    age_limit: Optional[str] = "Not mentioned"
    salary: Optional[str] = "Not mentioned"
    deadline: Optional[str] = "Open until filled"
    apply_link: str
    source_links: List[str] = Field(default_factory=list)
    primary_url: str
    eligibility_status: str  # "ELIGIBLE", "MAYBE", "NOT ELIGIBLE"
    eligibility_reason: str
    relevance_score: int = 50
    application_stage: str = "Saved"  # "Saved", "Applied", "Interview", "Rejected", "Offer"
    notes: str = ""
    application_date: Optional[str] = None
    fetched_at: str
    created_at: str


class ResearchGapModel(BaseModel):
    id: Optional[int] = None
    news_id: Optional[int] = None
    title: str
    topic: str
    gap_description: str
    tags: List[str] = Field(default_factory=list)
    status: str = "open"
    created_at: str


class DigestRunModel(BaseModel):
    id: Optional[int] = None
    run_time: str
    status: str
    news_count: int = 0
    jobs_count: int = 0
    subject: Optional[str] = None
    recipient_list: Optional[str] = None
    error_message: Optional[str] = None
