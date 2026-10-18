"""Unit tests for job deduplication and source link merging."""
import pytest
from database.connection import init_db, db_session
from jobs.fetchers.base_job_fetcher import RawJob
from jobs.eligibility.engine import EligibilityEvaluation
from jobs.store.job_repo import JobRepository


@pytest.fixture(autouse=True)
def setup_database():
    init_db()
    # Clear test jobs
    with db_session() as conn:
        conn.execute("DELETE FROM jobs WHERE organization LIKE 'TestOrg%';")


def test_job_deduplication_and_link_merge():
    eval1 = EligibilityEvaluation(
        status="ELIGIBLE",
        reason="MS CS required: OK. Max age 35: OK.",
        relevance_score=85,
        city="Lahore",
        job_type="Full-Time",
        qualification="MS CS",
        experience_desc="2 years",
        age_limit_desc="Max 35",
        deadline="30 Oct 2026",
        apply_link="https://testorg.pk/apply"
    )

    # Job from Source A (e.g. University Portal)
    job1 = RawJob(
        title="Lecturer in Data Science",
        organization="TestOrg Lahore",
        city="Lahore",
        url="https://testorg.pk/jobs/ds-lecturer",
        source_name="TestOrg Portal",
        extra_sources=[]
    )
    job_id1 = JobRepository.save_or_merge_job(job1, eval1)
    assert job_id1 is not None

    # Same job from Source B (e.g. Indeed PK)
    eval2 = EligibilityEvaluation(
        status="ELIGIBLE",
        reason="MS CS required: OK. Max age 35: OK.",
        relevance_score=85,
        city="Lahore",
        job_type="Full-Time",
        qualification="MS CS",
        experience_desc="2 years",
        age_limit_desc="Max 35",
        deadline="30 Oct 2026",
        apply_link="https://pk.indeed.com/viewjob?jk=12345"
    )
    job2 = RawJob(
        title="Lecturer in Data Science",
        organization="TestOrg Lahore",
        city="Lahore",
        url="https://pk.indeed.com/viewjob?jk=12345",
        source_name="Indeed PK",
        extra_sources=[]
    )
    job_id2 = JobRepository.save_or_merge_job(job2, eval2)

    # Must merge into the same job ID
    assert job_id2 == job_id1

    # Verify merged source links
    jobs = JobRepository.get_jobs(include_not_eligible=True)
    merged_job = next(j for j in jobs if j.id == job_id1)
    assert len(merged_job.source_links) >= 2
    assert "https://testorg.pk/jobs/ds-lecturer" in merged_job.source_links
    assert "https://pk.indeed.com/viewjob?jk=12345" in merged_job.source_links
