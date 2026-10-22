from datetime import datetime, timezone
from typing import List, Tuple
from fetchers.base import RawItem
from config.profile_loader import UserProfile


def score_item_relevance(item: RawItem, profile: UserProfile) -> int:
    """Compute a relevance score between 0 and 100 for an item relative to user profile."""
    score = 40  # Baseline for any tech item from our curated feeds

    text = f"{item.title} {item.summary} {item.content[:500]}".lower()

    # 1. Primary Research Interests (+25 to +35 pts)
    # Quantum Computing, NLP, LLMs
    if any(q in text for q in ["quantum", "qubit", "superconducting", "quant-ph"]):
        score += 30
    if any(nlp in text for nlp in ["nlp", "language model", "llm", "transformer", "prompt engineering", "retrieval augmented"]):
        score += 30
    if any(m in text for m in ["gpt-4", "gpt-5", "claude", "gemini", "deepseek", "llama", "grok", "mistral"]):
        score += 20

    # 2. Teaching & Academic / Placement Relevance (+15 to +20 pts)
    # Lecturer teaching programming, algorithms, CS education, training
    if any(ac in text for ac in ["algorithm", "data structure", "curriculum", "benchmark", "research gap", "arxiv", "paper"]):
        score += 15
    if any(code in text for code in ["python", "typescript", "framework", "fastapi", "react", "next.js", "docker"]):
        score += 15

    # 3. Source Prestige & Relevance Bonus (+10 pts)
    authoritative_sources = [
        "OpenAI Blog", "Google DeepMind Blog", "Google AI Blog", "Anthropic News",
        "arXiv", "MIT Technology Review", "AWS News Blog"
    ]
    if any(auth.lower() in item.source_name.lower() for auth in authoritative_sources):
        score += 10

    # 4. Podcast & Interview Takeaways (+10 pts)
    if item.extra.get("is_podcast"):
        score += 10

    # 5. Recency Boost & Stale Penalty (Fresh 24h news prioritized)
    if item.published_at:
        try:
            pub_dt = item.published_at
            if pub_dt.tzinfo is None:
                pub_dt = pub_dt.replace(tzinfo=timezone.utc)
            now_dt = datetime.now(timezone.utc)
            age_hours = (now_dt - pub_dt).total_seconds() / 3600.0
            if age_hours <= 24.0:
                score += 15  # Fresh breaking news today
            elif age_hours > 48.0:
                score -= 20  # Older news deprioritized
            elif age_hours > 96.0:
                score -= 35  # Stale news strongly demoted
        except Exception:
            pass

    # Clamp score between 10 and 100
    final_score = max(10, min(100, score))
    return final_score


def rank_and_filter_items(
    items: List[RawItem],
    profile: UserProfile,
    min_score: int = 40,
    top_limit: int = 25
) -> List[Tuple[RawItem, int]]:
    """Score all items, sort descending, and return top_limit items above min_score."""
    scored_items: List[Tuple[RawItem, int]] = []
    for item in items:
        score = score_item_relevance(item, profile)
        if score >= min_score:
            scored_items.append((item, score))

    scored_items.sort(key=lambda x: x[1], reverse=True)
    return scored_items[:top_limit]
