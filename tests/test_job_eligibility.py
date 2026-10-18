"""Unit tests for Job Eligibility Engine."""
import pytest
from config.profile_loader import load_profile
from jobs.fetchers.base_job_fetcher import RawJob
from jobs.eligibility.engine import EligibilityEngine


@pytest.fixture
def profile():
    return load_profile()


@pytest.fixture
def engine(profile):
    return EligibilityEngine(profile)


def test_eligible_job_all_match(engine):
    """Job requiring MS CS, 2 years experience, max age 35 -> ELIGIBLE."""
    job = RawJob(
        title="Lecturer in Computer Science",
        organization="GIFT University Gujranwala",
        city="Gujranwala",
        url="https://gift.edu.pk/jobs/1",
        source_name="GIFT Careers",
        description="Requires MS Computer Science. Minimum 2 years teaching experience. Maximum age 35 years.",
        raw_qualification="MS Computer Science",
        raw_experience="2 years experience required",
        raw_age_limit="Max 35 years"
    )
    res = engine.evaluate(job)
    assert res.status == "ELIGIBLE"
    assert "Max age 35, you are 28: OK" in res.reason
    assert "MS/MPhil required, you have MS/MPhil: OK" in res.reason
    assert "2.0 yrs required, you have 3.5 yrs: OK" in res.reason
    # Tier 1 city bonus (Gujranwala)
    assert res.relevance_score >= 80


def test_not_eligible_when_max_age_exceeded(engine):
    """Job with max age 25 (user is 28) -> NOT ELIGIBLE."""
    job = RawJob(
        title="Junior Teaching Assistant in CS",
        organization="University of the Punjab",
        city="Lahore",
        url="http://pu.edu.pk/jobs/2",
        source_name="PU Careers",
        description="Upper age limit strictly 25 years. MS in Computer Science.",
        raw_qualification="MS/MPhil",
        raw_age_limit="Max 25 years"
    )
    res = engine.evaluate(job)
    assert res.status == "NOT ELIGIBLE"
    assert "Max age 25, you are 28: Exceeds limit" in res.reason


def test_not_eligible_when_phd_mandatory(engine):
    """Job where PhD is mandatory (user has MS) -> NOT ELIGIBLE."""
    job = RawJob(
        title="Assistant Professor in AI",
        organization="FAST-NUCES",
        city="Lahore",
        url="https://nu.edu.pk/jobs/3",
        source_name="FAST Careers",
        description="PhD mandatory required in Computer Science or Artificial Intelligence from foreign university.",
        raw_qualification="PhD mandatory",
        raw_age_limit="Max 40 years"
    )
    res = engine.evaluate(job)
    assert res.status == "NOT ELIGIBLE"
    assert "PhD mandatory required, you have MS/MPhil: Not eligible" in res.reason


def test_not_eligible_when_experience_insufficient(engine):
    """Job requiring 10 years experience (user has 3.5 yrs) -> NOT ELIGIBLE."""
    job = RawJob(
        title="Senior Director IT Curriculum",
        organization="HEC",
        city="Islamabad",
        url="https://hec.gov.pk/jobs/4",
        source_name="HEC Careers",
        description="Candidate must have 10 years experience in academic leadership.",
        raw_qualification="MS/MPhil",
        raw_experience="10 years experience required",
        raw_age_limit="Max 45 years"
    )
    res = engine.evaluate(job)
    assert res.status == "NOT ELIGIBLE"
    assert "10.0 yrs" in res.reason
    assert "Insufficient" in res.reason


def test_maybe_when_age_or_qualification_not_mentioned(engine):
    """Job with unstated age or qualifications -> MAYBE with 'Not mentioned' reason."""
    job = RawJob(
        title="Trainer in Web Development",
        organization="Tech Training Institute",
        city="Lahore",
        url="https://tech.pk/jobs/5",
        source_name="Indeed PK",
        description="Looking for an energetic trainer to teach web development classes.",
        raw_qualification="Not mentioned",
        raw_age_limit="Not mentioned"
    )
    res = engine.evaluate(job)
    assert res.status == "MAYBE"
    assert "Age limit: Not mentioned" in res.reason
    assert "Qualification: Not mentioned" in res.reason
