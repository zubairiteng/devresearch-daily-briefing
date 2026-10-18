"""Base data structure for summarized briefing items."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class SummaryResult:
    headline: str
    summary_text: str
    why_it_matters: str
    research_gap: Optional[str] = None
