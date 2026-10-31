"""Unit tests for email digest rendering (HTML & Plain text)."""
import pytest
from datetime import datetime
from mailer.renderer import DigestRenderer
from database.models import NewsItemModel, JobItemModel


@pytest.fixture
def renderer():
    return DigestRenderer()


@pytest.fixture
def sample_news():
    return [
        NewsItemModel(
            id=1,
            title="OpenAI Unveils Reasoning Model Architecture",
            url="https://openai.com/news/reasoning",
            source_name="OpenAI Blog",
            category="ai_llm",
            summary="A deep dive into test-time compute scaling and verifier circuits.",
            why_it_matters="Directly relevant to AI agent workshops and undergraduate curriculum.",
            score=95,
            fetched_at="2026-10-18T10:00:00Z"
        ),
        NewsItemModel(
            id=2,
            title="FastAPI 0.115 Adds Enhanced Background Concurrency",
            url="https://fastapi.tiangolo.com/release",
            source_name="GitHub Releases",
            category="software_cloud",
            summary="FastAPI now introduces zero-allocation background task pipelines.",
            why_it_matters="Essential for backend services and student training.",
            score=82,
            fetched_at="2026-10-18T10:00:00Z"
        ),
        NewsItemModel(
            id=3,
            title="Fault-Tolerant Surface Codes on Quantum Processors",
            url="https://arxiv.org/abs/2610.11111",
            source_name="arXiv",
            category="research_watch",
            summary="Empirical threshold demonstration of 2D surface codes.",
            why_it_matters="Key paper for your active quantum research publications.",
            research_gap="Possible research gap: Benchmarking error syndromes under correlated cosmic noise.",
            score=90,
            fetched_at="2026-10-18T10:00:00Z"
        )
    ]


@pytest.fixture
def sample_jobs():
    return [
        JobItemModel(
            id=101,
            title="Lecturer in Computer Science",
            organization="GIFT University Gujranwala",
            city="Gujranwala",
            deadline="30 Oct 2026",
            apply_link="mailto:hr@gift.edu.pk",
            source_links=["https://gift.edu.pk/jobs/1"],
            primary_url="https://gift.edu.pk/jobs/1",
            eligibility_status="ELIGIBLE",
            eligibility_reason="Max age 35, you are 28: OK. MS CS required: OK. 2 yrs experience: OK.",
            relevance_score=92,
            fetched_at="2026-10-18T10:00:00Z",
            created_at="2026-10-18T10:00:00Z"
        ),
        JobItemModel(
            id=102,
            title="Technical Trainer AI",
            organization="NAVTTC",
            city="Lahore",
            deadline="05 Nov 2026",
            apply_link="https://navttc.gov.pk/apply",
            source_links=["https://navttc.gov.pk/jobs/2"],
            primary_url="https://navttc.gov.pk/jobs/2",
            eligibility_status="MAYBE",
            eligibility_reason="Age limit: Not mentioned. MS CS required: OK.",
            relevance_score=80,
            fetched_at="2026-10-18T10:00:00Z",
            created_at="2026-10-18T10:00:00Z"
        ),
        JobItemModel(
            id=103,
            title="Professor of Mathematics",
            organization="University of Lahore",
            city="Lahore",
            deadline="15 Nov 2026",
            apply_link="https://uol.edu.pk",
            source_links=["https://uol.edu.pk/jobs/3"],
            primary_url="https://uol.edu.pk/jobs/3",
            eligibility_status="NOT ELIGIBLE",
            eligibility_reason="PhD mandatory required: Not eligible.",
            relevance_score=30,
            fetched_at="2026-10-18T10:00:00Z",
            created_at="2026-10-18T10:00:00Z"
        )
    ]


def test_subject_line_format(renderer, sample_news, sample_jobs):
    fixed_date = datetime(2026, 10, 18)
    subject, html, txt = renderer.render_digest(
        news_items=sample_news,
        jobs=sample_jobs,
        closing_soon=[],
        date_obj=fixed_date
    )
    assert subject.startswith("DevResearch Daily | Oct 18, 2026 | ")
    assert "OpenAI Unveils Reasoning Model" in subject


def test_email_sections_and_job_filtering(renderer, sample_news, sample_jobs):
    subject, html, txt = renderer.render_digest(
        news_items=sample_news,
        jobs=sample_jobs,
        closing_soon=[sample_jobs[0]],
        read_later=[sample_news[0]]
    )

    # 1. Check sections exist in HTML
    assert "Today in Brief" in html
    assert "AI &amp; LLM Industry News" in html or "AI & LLM Industry News" in html
    assert "Software &amp; Cloud Development" in html or "Software & Cloud Development" in html
    assert "Research Watch &amp; Open Gaps" in html or "Research Watch & Open Gaps" in html
    assert "Jobs for You" in html
    assert "Closing Soon" in html
    assert "Your Saved Read Later List" in html

    # 2. Check research gap note is rendered
    assert "Possible research gap / opportunity:" in html
    assert "Benchmarking error syndromes" in html

    # 3. Check Jobs filtering: ELIGIBLE and MAYBE are present
    assert "Lecturer in Computer Science" in html
    assert "GIFT University Gujranwala" in html
    assert "Technical Trainer AI" in html
    assert "Max age 35, you are 28: OK" in html

    # 4. Strict check: NOT ELIGIBLE job MUST NEVER be in the email
    assert "Professor of Mathematics" not in html
    assert "NOT ELIGIBLE" not in html

    # 5. Check Plain-Text fallback
    assert "DEVRESEARCH DAILY BRIEFING" in txt
    assert "1. AI & LLM INDUSTRY NEWS" in txt
    assert "4. JOBS FOR YOU" in txt
    assert "Professor of Mathematics" not in txt


def test_render_error_alert(renderer):
    subj, html = renderer.render_error_alert("Database connection timeout after 3 retries.")
    assert "URGENT" in subj
    assert "Database connection timeout after 3 retries." in html



def test_render_urdu_digest(renderer, sample_news, sample_jobs):
    subj, html, txt = renderer.render_urdu_digest(
        news_items=sample_news,
        jobs=sample_jobs,
        closing_soon=[sample_jobs[0]],
        date_obj=datetime(2026, 10, 31)
    )

    # 1. Subject line format in Urdu
    assert "DevResearch Daily بریفنگ" in subj
    assert "اوپن اے آئی" in subj or "مسک" in subj

    # 2. RTL and Urdu language attributes
    assert 'dir="rtl"' in html
    assert 'lang="ur"' in html

    # 3. Core sections exist in Urdu
    assert "عالمی اے آئی و فرنٹیئر ٹیک انقلاب" in html
    assert "اکیڈمک واچ، ریسرچ گرانٹس اور IEEE کانفرنسز" in html
    assert "اشاعت کے لیے کھلے ریسرچ گیپس" in html
    assert "کیریئر و جابز واچ" in html

    # 4. Critical persona and entities mentioned
    assert "پروفیسر زبیر احمد" in html
    assert "ایلون مسک" in html
    assert "اوپن اے آئی" in html
    assert "اینتھروپک" in html
    assert "چائنا" in html
    assert "FIT" in html
    assert "IRSIP" in html
    assert "https://zubairiteng.github.io/devresearch-daily-briefing/" in html

    # 5. Text fallback in Urdu
    assert "ڈیو ریسرچ ڈیلی بریفنگ" in txt
    assert "آج کا کلیدی اداریہ" in txt
