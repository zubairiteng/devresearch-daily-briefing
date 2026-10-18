"""Jobs pipeline orchestrator for Pakistan."""
import asyncio
import logging
from typing import List
from config import load_profile, load_sources, UserProfile, AppSources
from jobs.fetchers import (
    RawJob, IndeedPKFetcher, UniversityJobFetcher,
    GovtSkillsJobFetcher, ImapJobAlertFetcher, RemoteAIJobFetcher
)
from jobs.eligibility.engine import EligibilityEngine
from jobs.store.job_repo import JobRepository
from database.models import JobItemModel

logger = logging.getLogger(__name__)


class JobsPipeline:
    def __init__(self, profile: UserProfile = None, sources: AppSources = None):
        self.profile = profile or load_profile()
        self.sources = sources or load_sources()
        self.engine = EligibilityEngine(self.profile)

    async def run(self) -> List[JobItemModel]:
        logger.info("Starting DevResearch Jobs Pipeline (Pakistan: Lahore & Gujranwala priority)...")

        # 1. Initialize fetchers
        fetchers = [
            IndeedPKFetcher(self.sources.jobs.pakistan_sources),
            UniversityJobFetcher(self.sources.jobs.pakistan_sources),
            GovtSkillsJobFetcher(self.sources.jobs.pakistan_sources),
            RemoteAIJobFetcher(getattr(self.sources.jobs, "remote_sources", [])),
            ImapJobAlertFetcher(self.sources.jobs.imap_email_alerts)
        ]

        # 2. Gather jobs
        tasks = [f.fetch() for f in fetchers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        raw_jobs: List[RawJob] = []
        for res in results:
            if isinstance(res, list):
                raw_jobs.extend(res)
            elif isinstance(res, Exception):
                logger.error(f"Job fetcher error: {res}")

        logger.info(f"Total raw jobs collected from Pakistan sources: {len(raw_jobs)}")

        # 3. Evaluate eligibility and store/merge
        saved_jobs: List[JobItemModel] = []
        for job in raw_jobs:
            eval_res = self.engine.evaluate(job)
            job_id = JobRepository.save_or_merge_job(job, eval_res)
            if job_id:
                links = [job.url] + job.extra_sources
                saved_jobs.append(
                    JobItemModel(
                        id=job_id,
                        title=job.title,
                        organization=job.organization,
                        city=eval_res.city,
                        job_type=eval_res.job_type,
                        required_qualification=eval_res.qualification,
                        required_experience=eval_res.experience_desc,
                        age_limit=eval_res.age_limit_desc,
                        salary=job.raw_salary or "Not mentioned",
                        deadline=eval_res.deadline,
                        apply_link=eval_res.apply_link,
                        source_links=links,
                        primary_url=job.url,
                        eligibility_status=eval_res.status,
                        eligibility_reason=eval_res.reason,
                        relevance_score=eval_res.relevance_score,
                        application_stage="Saved",
                        notes="",
                        fetched_at=job.fetched_at.isoformat() if job.fetched_at else "",
                        created_at=job.fetched_at.isoformat() if job.fetched_at else ""
                    )
                )

        logger.info(f"Jobs pipeline complete. Processed and saved {len(saved_jobs)} jobs.")
        return saved_jobs
