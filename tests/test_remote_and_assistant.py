"""Unit tests for Remote Jobs, Pakistan Exclusion, LinkedIn Alert parsing, Cover Letter, and Workflow."""
import pytest
import yaml
from pathlib import Path

from jobs.fetchers.remote_fetcher import detect_pakistan_eligibility
from jobs.fetchers.base_job_fetcher import RawJob
from jobs.eligibility.engine import EligibilityEngine
from config.profile_loader import load_profile
from jobs.apply_assistant.cv_parser import get_default_cv_profile
from jobs.apply_assistant.cover_letter import generate_tailored_cover_letter
from database.models import JobItemModel


def test_pakistan_excluded_detection():
    # 1. Hard exclusions
    allowed, reason = detect_pakistan_eligibility("US Only", "Must be located in the US.")
    assert allowed is False
    assert "Requires US residency" in reason

    allowed, reason = detect_pakistan_eligibility("EU Only", "Candidates in the European Union only.")
    assert allowed is False
    assert "Requires European Union residency" in reason

    allowed, reason = detect_pakistan_eligibility("Remote", "Excludes: PK applicants due to tax laws.")
    assert allowed is False
    assert "excludes applicants from Pakistan" in reason

    # 2. Worldwide / Pakistan friendly
    allowed, reason = detect_pakistan_eligibility("Worldwide", "Work from anywhere in the world.")
    assert allowed is True
    assert "Open to applicants from Pakistan" in reason

    allowed, reason = detect_pakistan_eligibility("Remote - Worldwide", "Global remote team.")
    assert allowed is True

    allowed, reason = detect_pakistan_eligibility("Remote (EMEA / Asia)", "Candidates in UTC+2 to UTC+6 welcome.")
    assert allowed is True


def test_remote_job_eligibility_engine():
    profile = load_profile()
    engine = EligibilityEngine(profile)

    # Job that excludes Pakistan
    job_us_only = RawJob(
        title="AI Engineer",
        organization="US Defense Corp",
        city="Remote",
        url="https://jobs.com/1",
        source_name="RemoteOK",
        description="US Citizen Only. Must be located in the US. MS CS required.",
        raw_qualification="MS Computer Science"
    )
    eval_res = engine.evaluate(job_us_only)
    assert eval_res.status == "NOT ELIGIBLE"
    assert "Pakistan excluded" in eval_res.reason

    # Job that is worldwide remote with age limit stated -> ELIGIBLE
    job_worldwide = RawJob(
        title="Generative AI Workflow Engineer",
        organization="Global AI Labs",
        city="Remote",
        url="https://jobs.com/2",
        source_name="RemoteOK",
        description="Worldwide remote. Open to all locations including Pakistan. Requires MS CS, 2 years Python and n8n experience. Max age 35 years.",
        raw_qualification="MS Computer Science",
        raw_experience="2 years experience required",
        raw_age_limit="Max 35 years"
    )
    eval_ww = engine.evaluate(job_worldwide)
    assert eval_ww.status == "ELIGIBLE"
    assert "Open to applicants from Pakistan" in eval_ww.reason
    assert eval_ww.relevance_score >= 80

    # Job that is worldwide remote but age limit unstated -> MAYBE (per section 5)
    job_no_age = RawJob(
        title="Generative AI Workflow Engineer",
        organization="Global AI Labs",
        city="Remote",
        url="https://jobs.com/2b",
        source_name="RemoteOK",
        description="Worldwide remote. Open to Pakistan.",
        raw_qualification="MS Computer Science",
        raw_experience="2 years experience required"
    )
    eval_no_age = engine.evaluate(job_no_age)
    assert eval_no_age.status == "MAYBE"
    assert "Age limit: Not mentioned" in eval_no_age.reason


def test_cover_letter_truthfulness_and_length():
    cv = get_default_cv_profile()
    job = JobItemModel(
        id=99,
        title="Agentic AI & Python Engineer",
        organization="Autoflow Labs",
        city="Remote",
        required_qualification="MS in Computer Science",
        required_experience="2 years Python and LLM agents",
        primary_url="https://autoflow.ai/jobs/1",
        apply_link="https://autoflow.ai/apply",
        eligibility_status="ELIGIBLE",
        eligibility_reason="MS CS required: OK.",
        relevance_score=90,
        fetched_at="2026-10-18T10:00:00Z",
        created_at="2026-10-18T10:00:00Z"
    )

    letter, matched, missing = generate_tailored_cover_letter(job, cv)

    # Check word count is between 120 and 280 words
    word_count = len(letter.split())
    assert 120 <= word_count <= 280

    # Ensure no fabricated claims
    assert cv.name in letter
    assert "MS Computer Science" in letter or "MS" in letter
    assert "In conclusion" not in letter
    assert "delve" not in letter.lower()

    # Check that skills mentioned exist in the CV
    cv_full_text = f"{' '.join(cv.skills)} {' '.join([e.get('details', '') for e in cv.experience])}".lower()
    for s in matched:
        assert s.lower() in cv_full_text


def test_workflow_config_syntax():
    workflow_path = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "daily.yml"
    assert workflow_path.exists()
    with open(workflow_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # In PyYAML, 'on' can parse as boolean True
    triggers = data.get("on") if "on" in data else data.get(True, {})
    schedule = triggers.get("schedule", [])
    assert any(s.get("cron") == "0 5 * * *" for s in schedule)
    assert "workflow_dispatch" in triggers

    # Verify steps contain pipeline run, database persistence, and pages deployment
    job_steps = data["jobs"]["run-pipeline-and-deploy"]["steps"]
    step_names = [s.get("name") for s in job_steps]
    assert any("Run Daily Briefing Pipeline" in n for n in step_names)
    assert any("Persist SQLite data.db" in n for n in step_names)
    assert any("Deploy to GitHub Pages" in n for n in step_names)
