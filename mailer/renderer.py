"""Template renderer for HTML and Plain-Text email digests (Easy English, Classic English & Urdu)."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from jinja2 import Environment, FileSystemLoader
from database.models import NewsItemModel, JobItemModel
from mailer.urdu_synthesizer import UrduDigestSynthesizer
from mailer.easy_english_synthesizer import EasyEnglishSynthesizer

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
        self.easy_en_html_tmpl = jinja_env.get_template("digest_easy_en.html")
        self.easy_en_txt_tmpl = jinja_env.get_template("digest_easy_en.txt")
        self.urdu_html_tmpl = jinja_env.get_template("digest_urdu.html")
        self.urdu_txt_tmpl = jinja_env.get_template("digest_urdu.txt")
        self.error_tmpl = jinja_env.get_template("error_alert.html")

    def render_easy_english_digest(
        self,
        news_items: List[NewsItemModel],
        jobs: List[JobItemModel],
        closing_soon: List[JobItemModel],
        date_obj: datetime = None
    ) -> Tuple[str, str, str]:
        """Renders clear, easy-to-read English daily briefing with layman explanations."""
        dt = date_obj or datetime.now()
        context = EasyEnglishSynthesizer.synthesize(
            news_items=news_items,
            jobs=jobs,
            closing_soon=closing_soon,
            date_obj=dt
        )
        subject = context["subject"]
        html_body = self.easy_en_html_tmpl.render(context)
        txt_body = self.easy_en_txt_tmpl.render(context)
        return subject, html_body, txt_body

    def render_urdu_digest(
        self,
        news_items: List[NewsItemModel],
        jobs: List[JobItemModel],
        closing_soon: List[JobItemModel],
        date_obj: datetime = None
    ) -> Tuple[str, str, str]:
        """Renders rich, mature Urdu daily briefing (subject, html, txt)."""
        dt = date_obj or datetime.now()
        context = UrduDigestSynthesizer.synthesize(
            news_items=news_items,
            jobs=jobs,
            closing_soon=closing_soon,
            date_obj=dt
        )
        subject = context["subject"]
        html_body = self.urdu_html_tmpl.render(context)
        txt_body = self.urdu_txt_tmpl.render(context)
        return subject, html_body, txt_body

    def render_digest(
        self,
        news_items: List[NewsItemModel],
        jobs: List[JobItemModel],
        closing_soon: List[JobItemModel],
        read_later: List[NewsItemModel] = None,
        date_obj: datetime = None,
        language: str = "en"
    ) -> Tuple[str, str, str]:
        """Returns (subject, html_content, text_content). Defaults to English for backwards compatibility."""
        if language in ("easy_en", "easy", "plain_en"):
            return self.render_easy_english_digest(
                news_items=news_items,
                jobs=jobs,
                closing_soon=closing_soon,
                date_obj=date_obj
            )

        if language == "ur":
            return self.render_urdu_digest(
                news_items=news_items,
                jobs=jobs,
                closing_soon=closing_soon,
                date_obj=date_obj
            )

        dt = date_obj or datetime.now()
        date_str = dt.strftime("%A, %B %d, %Y")

        # Categorize news items
        ai_items = [n for n in news_items if n.category == "ai_llm"]
        dev_items = [n for n in news_items if n.category == "software_cloud"]
        research_items = [n for n in news_items if n.category == "research_watch"]

        # Subject: DevResearch Daily | <date> | <top headline>
        top_headline = "Latest AI, Dev, Research & Jobs Updates"
        if news_items:
            fresh_candidate = None
            for item in news_items:
                if "Release:" not in item.title:
                    fresh_candidate = item.title
                    break
            if fresh_candidate:
                words = fresh_candidate.split()
                top_headline = " ".join(words[:10])

        short_date = dt.strftime("%b %d, %Y")
        subject = f"DevResearch Daily | {short_date} | {top_headline}"

        # 3-bullet summary for 'Today in Brief'
        today_in_brief = []
        if ai_items:
            today_in_brief.append(f"AI & LLMs: {ai_items[0].title}")
        if dev_items:
            today_in_brief.append(f"Cloud/Dev: {dev_items[0].title}")
        if research_items:
            today_in_brief.append(f"Research: {research_items[0].title}")
        if not today_in_brief:
            today_in_brief = [
                "New models and updates gathered across AI labs.",
                "Cloud infrastructure releases and tooling updates.",
                "Latest papers evaluated for quantum and NLP research."
            ]

        # Rotate tech quote of the day
        quote_index = dt.timetuple().tm_yday % len(CURATED_TECH_QUOTES)
        quote_of_the_day = CURATED_TECH_QUOTES[quote_index]

        # Filter jobs for email (strictly exclude NOT ELIGIBLE)
        eligible_jobs = [j for j in jobs if j.eligibility_status in ("ELIGIBLE", "MAYBE")]

        context = {
            "subject": subject,
            "date_str": date_str,
            "today_in_brief": today_in_brief,
            "ai_items": ai_items[:6],
            "dev_items": dev_items[:5],
            "research_items": research_items[:5],
            "new_jobs": eligible_jobs[:8],
            "closing_soon_jobs": closing_soon,
            "read_later_items": (read_later or [])[:5],
            "quote": quote_of_the_day,
            "dashboard_url": "https://zubairiteng.github.io/devresearch-daily-briefing/"
        }

        html_body = self.html_tmpl.render(context)
        txt_body = self.txt_tmpl.render(context)

        return subject, html_body, txt_body

    def render_error_alert(self, error_message: str) -> Tuple[str, str]:
        """Renders critical failure alert sent when briefing fails all retries."""
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        subject = f"[URGENT] DevResearch Daily Briefing Failed - {now_str}"
        html_body = self.error_tmpl.render({
            "timestamp": now_str,
            "error_message": error_message,
            "docs_url": "https://github.com/zubairiteng/devresearch-daily-briefing"
        })
        return subject, html_body
