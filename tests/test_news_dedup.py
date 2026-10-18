"""Unit tests for news deduplication and URL normalization."""
import pytest
from fetchers.base import RawItem
from processors.deduplicator import normalize_url, compute_title_similarity, deduplicate_news


def test_normalize_url():
    url_with_utm = "https://techcrunch.com/2026/10/18/ai-announcement/?utm_source=twitter&utm_medium=social#comments"
    clean = normalize_url(url_with_utm)
    assert "utm_source" not in clean
    assert "comments" not in clean
    assert clean == "https://techcrunch.com/2026/10/18/ai-announcement"


def test_compute_title_similarity():
    t1 = "OpenAI releases GPT-4o with real-time audio and vision"
    t2 = "OpenAI Launches GPT-4o with Real-Time Audio and Vision Capabilities"
    sim = compute_title_similarity(t1, t2)
    assert sim >= 0.65

    t3 = "Quantum computing milestone reached by Google Quantum AI team"
    sim_diff = compute_title_similarity(t1, t3)
    assert sim_diff < 0.20


def test_deduplicate_news():
    items = [
        RawItem(
            title="Claude 3.5 Sonnet released by Anthropic",
            url="https://anthropic.com/news/claude-3-5?utm_source=feed",
            source_name="Anthropic News",
            content="Anthropic announced Claude 3.5 Sonnet with state-of-the-art coding abilities."
        ),
        RawItem(
            title="Anthropic releases Claude 3.5 Sonnet model",
            url="https://techcrunch.com/2026/claude-3-5",
            source_name="TechCrunch",
            content="Anthropic today launched Claude 3.5 Sonnet."
        ),
        RawItem(
            title="Fault-Tolerant Quantum Computing Paper on arXiv",
            url="https://arxiv.org/abs/2610.12345",
            source_name="arXiv",
            content="A novel quantum error correction threshold theorem."
        )
    ]

    deduped = deduplicate_news(items, similarity_threshold=0.60)
    # The two Claude items should be merged into 1
    assert len(deduped) == 2
    titles = [i.title for i in deduped]
    assert any("Claude" in t for t in titles)
    assert any("Quantum" in t for t in titles)
    # Merged sources check
    claude_item = next(i for i in deduped if "Claude" in i.title)
    assert "Anthropic" in claude_item.source_name
