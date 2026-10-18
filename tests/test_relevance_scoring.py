"""Unit tests for relevance scoring against UserProfile."""
import pytest
from fetchers.base import RawItem
from config.profile_loader import load_profile
from processors.scorer import score_item_relevance, rank_and_filter_items


def test_score_quantum_item_is_high():
    profile = load_profile()
    item = RawItem(
        title="Scalable Quantum Error Correction with Neutral Atoms",
        url="https://arxiv.org/abs/2610.99999",
        source_name="arXiv",
        content="We demonstrate fault-tolerant quantum logical qubits using superconducting quantum circuits."
    )
    score = score_item_relevance(item, profile)
    # Quantum is primary research interest (+30) + arXiv (+10) + baseline (40) => >= 75
    assert score >= 75


def test_score_nlp_llm_item_is_high():
    profile = load_profile()
    item = RawItem(
        title="DeepSeek-R1: Incentivizing Reasoning in LLMs via Reinforcement Learning",
        url="https://github.com/deepseek-ai/DeepSeek-R1",
        source_name="GitHub Releases",
        content="DeepSeek introduces an open-weights reasoning model with high performance on mathematical benchmarks."
    )
    score = score_item_relevance(item, profile)
    assert score >= 75


def test_score_cloud_dev_relevance():
    profile = load_profile()
    item = RawItem(
        title="Next.js 15 and React 19 Server Components Architecture",
        url="https://nextjs.org/blog/next-15",
        source_name="Vercel",
        content="Explore the latest features in web development and full-stack rendering."
    )
    score = score_item_relevance(item, profile)
    assert 50 <= score <= 85


def test_rank_and_filter_items():
    profile = load_profile()
    items = [
        RawItem(title="Generic news article about electric cars", url="http://a.com", source_name="News", content="Cars"),
        RawItem(title="Quantum computing state of the art in 2026", url="http://b.com", source_name="arXiv", content="Quantum"),
        RawItem(title="LLM Prompt Tuning for University Curriculum", url="http://c.com", source_name="OpenAI Blog", content="LLM"),
    ]
    ranked = rank_and_filter_items(items, profile, min_score=30, top_limit=2)
    assert len(ranked) == 2
    # The top scored should be Quantum or LLM
    top_title = ranked[0][0].title
    assert "Quantum" in top_title or "LLM" in top_title
