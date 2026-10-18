"""Summarizer package."""
from .base import SummaryResult
from .heuristic import generate_heuristic_summary
from .llm_adapter import LLMSummarizer

__all__ = ["SummaryResult", "generate_heuristic_summary", "LLMSummarizer"]
