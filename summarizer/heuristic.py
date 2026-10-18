"""Intelligent heuristic and extractive summarizer enforcing conversational human style."""
import re
from typing import Optional
from fetchers.base import RawItem
from config.profile_loader import UserProfile
from .base import SummaryResult

FORBIDDEN_PHRASES = [
    "in conclusion", "it is worth noting", "delve", "furthermore", "moreover",
    "testament to", "revolutionize", "tapestry", "beacon", "game-changer", "dive into"
]


def clean_text_from_ai_cliches(text: str) -> str:
    """Strip robotic AI phrases and formatting cliches."""
    cleaned = text
    for phrase in FORBIDDEN_PHRASES:
        pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
        cleaned = pattern.sub("", cleaned)
    # Remove multiple spaces
    return " ".join(cleaned.split())


def generate_heuristic_summary(item: RawItem, category: str, profile: UserProfile) -> SummaryResult:
    """Generate conversational human-colleague summary without robotic jargon."""
    raw_content = item.content or item.summary or item.title
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", raw_content) if len(s.strip()) > 15]

    # Headline: Keep it catchy, human, and direct
    clean_title = re.sub(r"^(Show HN:|Ask HN:|\[.*?\])\s*", "", item.title).strip()
    headline = clean_title

    # Extract 2-3 strongest informative sentences
    if len(sentences) >= 3:
        summary_body = " ".join(sentences[:3])
    elif len(sentences) >= 1:
        summary_body = " ".join(sentences)
    else:
        summary_body = f"{item.title}. Details announced via {item.source_name}."

    summary_body = clean_text_from_ai_cliches(summary_body)

    # Why it matters to you (tailored to Lecturer, Placement Officer, NAVTTC, and Researcher)
    text_lower = f"{item.title} {summary_body}".lower()
    why_it_matters = ""
    research_gap: Optional[str] = None

    if category == "research_watch" or "arxiv" in item.source_name.lower():
        if "quantum" in text_lower:
            why_it_matters = "Directly relevant to your quantum research agenda; highlights state-of-the-art benchmarks in qubit stability and algorithmic design."
            research_gap = "Potential research gap: Evaluating noise resistance and error mitigation when interfacing this architecture with hybrid classical-quantum pipelines."
        elif "llm" in text_lower or "nlp" in text_lower or "language" in text_lower:
            why_it_matters = "Useful for your NLP lectures and ongoing publications on efficient model architectures."
            research_gap = "Possible publication opportunity: Investigating sample efficiency and domain adaptation across low-resource dialects or localized educational datasets."
        else:
            why_it_matters = "Valuable for updating your CS coursework curriculum and guiding university final-year projects."
            research_gap = "Open research opportunity: Exploring empirical trade-offs between computational overhead and inference latency in production deployment."

    elif category == "ai_llm":
        if "deepseek" in text_lower or "llama" in text_lower or "qwen" in text_lower or "open" in text_lower:
            why_it_matters = "Key open-weight milestone that gives your university lab and students locally hosted alternatives without reliance on proprietary APIs."
        elif "openai" in text_lower or "anthropic" in text_lower or "gemini" in text_lower:
            why_it_matters = "Sets the baseline capabilities for agentic reasoning and tool use you can incorporate into hands-on student workshops."
        else:
            why_it_matters = "Keeps you ahead of the fast-moving tech race, from hardware bottlenecks to emerging model capabilities."

    else:  # software_cloud
        if any(w in text_lower for w in ["react", "next.js", "frontend", "web"]):
            why_it_matters = "Directly applicable to full-stack student training modules and modern web application development."
        elif any(c in text_lower for c in ["aws", "azure", "gcp", "docker", "kubernetes", "cloud"]):
            why_it_matters = "Essential for updating practical cloud labs and NAVTTC vocational training syllabi with industry-standard tooling."
        else:
            why_it_matters = "Boosts developer productivity and offers immediate utility for local engineering projects."

    return SummaryResult(
        headline=headline,
        summary_text=summary_body,
        why_it_matters=why_it_matters,
        research_gap=research_gap
    )
