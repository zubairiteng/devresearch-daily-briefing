"""Processors package."""
from .deduplicator import deduplicate_news, compute_title_similarity, normalize_url
from .classifier import classify_item
from .scorer import score_item_relevance, rank_and_filter_items

__all__ = [
    "deduplicate_news",
    "compute_title_similarity",
    "normalize_url",
    "classify_item",
    "score_item_relevance",
    "rank_and_filter_items",
]
