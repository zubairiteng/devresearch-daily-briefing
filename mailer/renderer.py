"""Template renderer for HTML and Plain-Text email digests."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from jinja2 import Environment, FileSystemLoader
from database.models import NewsItemModel, JobItemModel

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True
)

CURATED_TECH_QUOTES = [
    {
        "text": "The bottleneck for artificial intelligence is shifting rapidly from raw model scale to test-time compute, reasoning verification, and high-quality synthetic data.",
        "author": "Ilya Sutskever",
        "show": "Safe Superintelligence / NeurIPS Dialogue"
    },
    {
        "text": "Open weights are critical for the democratization of computing. When educators and researchers have access to models locally, innovation accelerates everywhere.",
        "author": "Yann LeCun",
        "show": "Lex Fridman Podcast"
    },
    {
        "text": "The future of software engineering isn't writing boilerplate code; it's architecting systems, specifying invariants, and orchestrating intelligent agents.",
        "author": "Andrej Karpathy",
        "show": "Latent Space AI Podcast"
    },
    {
        "text": "In quantum computing, physical qubit counts grab headlines, but logical error-corrected qubits and transversal gate fidelity are the real milestones.",
        "author": "John Preskill",
        "show": "Caltech Quantum Colloquium"
    }
]


class DigestRenderer:
    def __init__(self):
        self.html_tmpl = jinja_env.get_template("digest.html")
        self.txt_tmpl = jinja_env.get_template("digest.txt")
        self.error_tmpl = jinja_env.get_template("error_alert.html")

    def render_digest(
        self,
        news_items: List[NewsItemModel],
        jobs: List[JobItemModel],
        closing_soon: List[JobItemModel],
        read_later: List[NewsItemModel] = None,
        date_obj: datetime = None
    ) -> Tuple[str, str, str]:
        """Returns (subject, html_content, text_content)."""
        dt = date_obj or datetime.now()
        date_str = dt.strftime("%A, %B %d, %Y")

        # Categorize news items
        ai_items = [n for n in news_items if n.category == "ai_llm"]
        dev_items = [n for n in news_items if n.category == "software_cloud"]
        research_items = [n for n in news_items if n.category == "research_watch"]

        # Subject: DevResearch Daily | <date> | <top headline>
        top_headline = "Latest AI, Dev, Research & Jobs Updates"
        if news_items:
            top_headline = news_items[0].title
            # Strip prefixes if any
            if len(top_headline) > 65:
                top_headline = top_headline[:62] + "..."

        subject = f"DevResearch Daily | {dt.strftime('%b %d, %Y')} | {top_headline}"

        # 1. Today in brief (3 lines)
        today_in_brief = []
        if ai_items:
            today_in_brief.append(f"AI/LLM: {ai_items[0].title}")
        if dev_items:
            today_in_brief.append(f"Software & Cloud: {dev_items[0].title}")
        if research_items:
            today_in_brief.append(f"Research: {research_items[0].title}")
        while len(today_in_brief) < 3 and len(news_items) > len(today_in_brief):
            today_in_brief.append(news_items[len(today_in_brief)].title)
        if not today_in_brief:
            today_in_brief = [
                "Comprehensive review of LLM releases, cloud frameworks, and quantum research.",
                "Targeted job opportunities in Lahore, Gujranwala, and academic institutions.",
                "Identified open research gaps ready for publication."
            ]

        # 5. Filter Jobs: Only ELIGIBLE or MAYBE, NEVER NOT ELIGIBLE.
        # Split into Pakistan (Lahore/Gujranwala first) and Remote & AI jobs
        pakistan_jobs = [j for j in jobs if j.city != "Remote" and j.eligibility_status in ("ELIGIBLE", "MAYBE")]
        pakistan_jobs.sort(key=lambda j: (0 if j.eligibility_status == "ELIGIBLE" else 1, -j.relevance_score))

        remote_ai_jobs = [j for j in jobs if j.city == "Remote" and j.eligibility_status in ("ELIGIBLE", "MAYBE")]
        remote_ai_jobs.sort(key=lambda j: (0 if j.eligibility_status == "ELIGIBLE" else 1, -j.relevance_score))

        # Quote of the day (cycled based on day of year)
        quote_idx = dt.timetuple().tm_yday % len(CURATED_TECH_QUOTES)
        quote = CURATED_TECH_QUOTES[quote_idx]

        context: Dict[str, Any] = {
            "subject": subject,
            "date_str": date_str,
            "today_in_brief": today_in_brief[:3],
            "ai_items": ai_items,
            "dev_items": dev_items,
            "research_items": research_items,
            "new_jobs": pakistan_jobs,
            "remote_ai_jobs": remote_ai_jobs,
            "closing_soon_jobs": closing_soon,
            "quote": quote,
            "read_later_items": read_later or []
        }

        html_body = self.html_tmpl.render(context)
        txt_body = self.txt_tmpl.render(context)

        return subject, html_body, txt_body

    def render_error_alert(self, error_message: str) -> Tuple[str, str]:
        subject = "URGENT: DevResearch Daily Briefing Pipeline Alert"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html_body = self.error_tmpl.render(
            error_message=error_message,
            timestamp=now_str
        )
        return subject, html_body
