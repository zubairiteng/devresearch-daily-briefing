"""Category classifier for DevResearch items."""
import re
from fetchers.base import RawItem

AI_KEYWORDS = [
    "llm", "large language model", "gpt", "chatgpt", "openai", "claude", "anthropic",
    "gemini", "deepmind", "deepseek", "llama", "meta ai", "mistral", "grok", "xai",
    "qwen", "transformer", "diffusion", "rag", "fine-tuning", "quantization", "prompt",
    "agent", "synthetic data", "gpu", "nvidia", "cuda", "musk", "tesla", "robotics"
]

RESEARCH_KEYWORDS = [
    "quantum", "qubit", "quantum computing", "arxiv", "paper", "novel algorithm",
    "benchmark", "empirical evaluation", "ablation", "theorem", "state of the art",
    "sota", "cs.cl", "cs.ai", "cs.lg", "quant-ph", "research gap", "conference", "neurips",
    "icml", "acl", "emnlp", "cvpr"
]

CLOUD_DEV_KEYWORDS = [
    "react", "next.js", "vue", "javascript", "typescript", "python", "rust", "golang",
    "aws", "azure", "google cloud", "gcp", "serverless", "kubernetes", "docker",
    "devops", "ci/cd", "api", "fastapi", "framework", "database", "postgres", "sqlite",
    "web development", "backend", "frontend", "git"
]


def classify_item(item: RawItem) -> str:
    """Classify item into ai_llm, software_cloud, or research_watch."""
    # Check explicit extra tags first
    if item.extra.get("is_research_paper") or "quant-ph" in str(item.extra):
        return "research_watch"

    combined_text = f"{item.title} {item.summary} {item.content[:500]}".lower()

    # Score matches
    ai_score = sum(1 for kw in AI_KEYWORDS if re.search(r"\b" + re.escape(kw) + r"\b", combined_text))
    research_score = sum(1 for kw in RESEARCH_KEYWORDS if re.search(r"\b" + re.escape(kw) + r"\b", combined_text))
    cloud_score = sum(1 for kw in CLOUD_DEV_KEYWORDS if re.search(r"\b" + re.escape(kw) + r"\b", combined_text))

    # arXiv or paper mentions
    if "arxiv" in combined_text or "quantum" in combined_text:
        research_score += 3

    scores = [
        ("ai_llm", ai_score),
        ("research_watch", research_score),
        ("software_cloud", cloud_score)
    ]
    # Sort descending by match score
    scores.sort(key=lambda x: x[1], reverse=True)

    if scores[0][1] > 0:
        return scores[0][0]

    # Fallback to existing item category
    return item.category or "ai_llm"
