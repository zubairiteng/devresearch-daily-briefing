"""Export a privacy-sanitized, static, read-only dashboard for GitHub Pages."""
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database.connection import get_db_connection
from database.news_repo import NewsRepository
from jobs.store.job_repo import JobRepository

DIST_DIR = BASE_DIR / "dist"
FRONTEND_HTML_PATH = BASE_DIR / "frontend" / "index.html"
logger = logging.getLogger(__name__)


def export_sanitized_static_dashboard() -> Path:
    """Builds a standalone public static dashboard in dist/index.html with ZERO private data."""
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Fetch public news, research gaps, and public jobs
    news_items = NewsRepository.get_latest_news(limit=60)
    ai_items = [n.model_dump() for n in news_items if n.category == "ai_llm"]
    dev_items = [n.model_dump() for n in news_items if n.category == "software_cloud"]
    research_items = [n.model_dump() for n in news_items if n.category == "research_watch"]
    gaps = [g.model_dump() for g in NewsRepository.get_research_gaps()]

    # Jobs: Filter out private tracker notes or personal data
    raw_jobs = JobRepository.get_jobs(include_not_eligible=True, limit=100)
    sanitized_jobs = []
    for j in raw_jobs:
        jd = j.model_dump()
        jd["notes"] = ""  # Strip private application notes
        jd["application_date"] = None
        sanitized_jobs.append(jd)

    closing_soon = [j.model_dump() for j in JobRepository.get_closing_soon_jobs(days_window=5)]
    for c in closing_soon:
        c["notes"] = ""

    static_data_json = json.dumps({
        "date": datetime.now(timezone.utc).strftime("%A, %B %d, %Y"),
        "counts": {
            "ai": len(ai_items),
            "dev": len(dev_items),
            "research": len(research_items),
            "jobs": len(sanitized_jobs)
        },
        "ai_items": ai_items,
        "dev_items": dev_items,
        "research_items": research_items,
        "jobs": sanitized_jobs,
        "gaps": gaps,
        "closing_soon": closing_soon,
        "is_static_public": True
    })

    # 2. Read template and inject static embedded data
    with open(FRONTEND_HTML_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Inject static bootstrapping script before </head>
    bootstrap_script = f"""
    <script>
      window.STATIC_PUBLIC_MODE = true;
      window.STATIC_DATA = {static_data_json};

      // Mock API calls in static public mode using localStorage for client-side state
      const origFetch = window.fetch;
      window.fetch = async function(url, options) {{
        const u = url.toString();
        if (u.includes('/api/digest/today')) {{
          return {{ ok: true, json: async () => window.STATIC_DATA }};
        }}
        if (u.includes('/api/digest/history')) {{
          return {{ ok: true, json: async () => ({{ count: window.STATIC_DATA.ai_items.length + window.STATIC_DATA.dev_items.length + window.STATIC_DATA.research_items.length, items: [...window.STATIC_DATA.ai_items, ...window.STATIC_DATA.dev_items, ...window.STATIC_DATA.research_items] }}) }};
        }}
        if (u.includes('/api/research-gaps')) {{
          return {{ ok: true, json: async () => ({{ count: window.STATIC_DATA.gaps.length, gaps: window.STATIC_DATA.gaps }}) }};
        }}
        if (u.includes('/api/jobs')) {{
          if (options && options.method === 'POST') {{
            return {{ ok: true, json: async () => ({{ success: true }}) }};
          }}
          return {{ ok: true, json: async () => ({{ count: window.STATIC_DATA.jobs.length, jobs: window.STATIC_DATA.jobs, closing_soon: window.STATIC_DATA.closing_soon }}) }};
        }}
        if (u.includes('/api/settings')) {{
          return {{ ok: true, json: async () => ({{
            profile: {{ education: {{ degree: 'MS Computer Science' }}, personal: {{ birth_date: '1998-05-15' }}, experience_years: {{ teaching: 3.5, industry: 2.5, placement_and_training: 2.0 }}, locations: {{ tier_1: ['Lahore', 'Gujranwala'] }} }},
            sources: {{}},
            delivery: {{ digest_time: '10:00', timezone: 'Asia/Karachi', mail_recipients: 'user@example.com', mail_provider: 'smtp' }}
          }}) }};
        }}
        if (u.includes('/api/pipeline/run') || u.includes('/api/email/test')) {{
          return {{ ok: true, json: async () => ({{ success: true, message: 'Public Read-Only Mirror: Live execution is managed locally on your machine.' }}) }};
        }}
        if (u.includes('/api/apply')) {{
          return {{ ok: true, json: async () => ({{
            job: {{ title: 'Position', organization: 'Organization', city: 'Lahore' }},
            cover_letter: 'Public mirror preview: tailored cover letters and CV generation are created on your private local dashboard.',
            matched_skills: ['Python', 'AI', 'Teaching'],
            missing_skills: [],
            cv_filename: 'CV_Sample.pdf',
            download_url: '#',
            is_email_apply: false
          }}) }};
        }}
        return origFetch(url, options);
      }};
    </script>
    """

    static_html = html_content.replace("</head>", f"{bootstrap_script}\n</head>")

    dist_file = DIST_DIR / "index.html"
    with open(dist_file, "w", encoding="utf-8") as f:
        f.write(static_html)

    logger.info(f"Generated sanitized static public dashboard: {dist_file}")
    return dist_file


if __name__ == "__main__":
    export_sanitized_static_dashboard()
