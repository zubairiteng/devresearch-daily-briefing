"""API Integration and endpoint unit tests."""
import pytest
from fastapi.testclient import TestClient
from api.main import app
from database.connection import init_db
from jobs.fetchers.base_job_fetcher import RawJob
from jobs.eligibility.engine import EligibilityEvaluation
from jobs.store.job_repo import JobRepository

client = TestClient(app)


@pytest.fixture(autouse=True)
def init_test_db():
    init_db()


def test_get_today_digest():
    response = client.get("/api/digest/today")
    assert response.status_code == 200
    data = response.json()
    assert "counts" in data
    assert "ai_items" in data
    assert "dev_items" in data
    assert "research_items" in data
    assert "top_jobs" in data


def test_get_history():
    response = client.get("/api/digest/history?category=all")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "items" in data


def test_get_research_gaps():
    response = client.get("/api/research-gaps")
    assert response.status_code == 200
    data = response.json()
    assert "gaps" in data


def test_get_jobs_and_stage_update():
    # Insert a job first
    eval_res = EligibilityEvaluation(
        status="ELIGIBLE",
        reason="MS CS required: OK.",
        relevance_score=85,
        city="Lahore",
        job_type="Full-Time",
        qualification="MS CS",
        experience_desc="2 yrs",
        age_limit_desc="Max 35",
        deadline="25 Oct 2026",
        apply_link="https://job.pk/apply"
    )
    job = RawJob(
        title="Software Lecturer Test",
        organization="Test University Lahore",
        city="Lahore",
        url="https://job.pk/123",
        source_name="Test Source"
    )
    job_id = JobRepository.save_or_merge_job(job, eval_res)

    # 1. Query jobs
    resp = client.get("/api/jobs?city=Lahore")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1

    # 2. Update stage to Applied
    update_resp = client.post(f"/api/jobs/{job_id}/stage", json={"stage": "Applied", "notes": "Submitted CV"})
    assert update_resp.status_code == 200
    assert update_resp.json()["new_stage"] == "Applied"


def test_get_and_update_settings():
    # Get settings
    resp = client.get("/api/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert "profile" in data
    assert "sources" in data
    assert "delivery" in data

    # Update profile (age calculation test)
    profile_update = data["profile"]
    profile_update["personal"]["birth_date"] = "1998-05-15"
    post_resp = client.post("/api/settings/profile", json=profile_update)
    assert post_resp.status_code == 200
    assert post_resp.json()["success"] is True
    assert "calculated_age" in post_resp.json()
