"""Database repository for Pakistani job postings and application tracker."""
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from database.connection import db_session
from database.models import JobItemModel
from jobs.fetchers.base_job_fetcher import RawJob
from jobs.eligibility.engine import EligibilityEvaluation
from processors.deduplicator import normalize_title, compute_title_similarity, normalize_url


class JobRepository:
    @staticmethod
    def save_or_merge_job(job: RawJob, eval_result: EligibilityEvaluation) -> Optional[int]:
        now_str = datetime.now(timezone.utc).isoformat()
        clean_url = normalize_url(job.url)

        with db_session() as conn:
            cursor = conn.cursor()

            # Check if this exact URL exists
            cursor.execute("SELECT id, source_links FROM jobs WHERE primary_url = ?", (clean_url,))
            existing = cursor.fetchone()

            # If not exact URL, check if same job exists by title + org fuzzy similarity
            if not existing:
                cursor.execute("SELECT id, title, organization, primary_url, source_links FROM jobs")
                all_jobs = cursor.fetchall()
                for ej in all_jobs:
                    # Check title similarity and organization match
                    org_match = (ej["organization"].lower().strip() == job.organization.lower().strip())
                    title_sim = compute_title_similarity(ej["title"], job.title)
                    if org_match and title_sim >= 0.70:
                        existing = ej
                        break

            if existing:
                # Merge source links
                existing_links = json.loads(existing["source_links"]) if existing["source_links"] else []
                if clean_url not in existing_links:
                    existing_links.append(clean_url)
                for extra in job.extra_sources:
                    c_extra = normalize_url(extra)
                    if c_extra not in existing_links:
                        existing_links.append(c_extra)

                cursor.execute("""
                    UPDATE jobs SET
                        source_links = ?,
                        eligibility_status = ?,
                        eligibility_reason = ?,
                        relevance_score = ?,
                        deadline = COALESCE(?, deadline),
                        apply_link = COALESCE(?, apply_link)
                    WHERE id = ?
                """, (
                    json.dumps(existing_links),
                    eval_result.status,
                    eval_result.reason,
                    eval_result.relevance_score,
                    eval_result.deadline if eval_result.deadline != "Not mentioned" else None,
                    eval_result.apply_link,
                    existing["id"]
                ))
                return existing["id"]

            # Insert fresh job
            all_source_links = [clean_url] + [normalize_url(s) for s in job.extra_sources if s]
            cursor.execute("""
                INSERT INTO jobs (
                    title, organization, city, job_type, required_qualification,
                    required_experience, age_limit, salary, deadline, apply_link,
                    source_links, primary_url, eligibility_status, eligibility_reason,
                    relevance_score, application_stage, notes, fetched_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Saved', '', ?, ?)
            """, (
                job.title,
                job.organization,
                eval_result.city,
                eval_result.job_type,
                eval_result.qualification,
                eval_result.experience_desc,
                eval_result.age_limit_desc,
                job.raw_salary or "Not mentioned",
                eval_result.deadline,
                eval_result.apply_link,
                json.dumps(list(set(all_source_links))),
                clean_url,
                eval_result.status,
                eval_result.reason,
                eval_result.relevance_score,
                now_str,
                now_str
            ))
            return cursor.lastrowid

    @staticmethod
    def get_jobs(
        city: Optional[str] = None,
        eligibility_status: Optional[str] = None,
        stage: Optional[str] = None,
        include_not_eligible: bool = False,
        limit: int = 100
    ) -> List[JobItemModel]:
        with db_session() as conn:
            cursor = conn.cursor()
            sql = "SELECT * FROM jobs WHERE 1=1"
            params: List[Any] = []

            if not include_not_eligible and not eligibility_status:
                sql += " AND eligibility_status != 'NOT ELIGIBLE'"
            elif eligibility_status and eligibility_status != "all":
                sql += " AND eligibility_status = ?"
                params.append(eligibility_status)

            if city and city != "all":
                sql += " AND city LIKE ?"
                params.append(f"%{city}%")

            if stage and stage != "all":
                sql += " AND application_stage = ?"
                params.append(stage)

            sql += " ORDER BY relevance_score DESC, id DESC LIMIT ?"
            params.append(limit)

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [JobRepository._row_to_model(r) for r in rows]

    @staticmethod
    def get_jobs_for_digest(lookback_hours: int = 24) -> List[JobItemModel]:
        """Fetch only new jobs from the last 24h that are ELIGIBLE or MAYBE, sorted by relevance, ELIGIBLE first."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=lookback_hours)).isoformat()
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM jobs
                WHERE fetched_at >= ?
                  AND eligibility_status IN ('ELIGIBLE', 'MAYBE')
                ORDER BY
                  CASE WHEN eligibility_status = 'ELIGIBLE' THEN 0 ELSE 1 END,
                  relevance_score DESC
            """, (cutoff,))
            rows = cursor.fetchall()
            return [JobRepository._row_to_model(r) for r in rows]

    @staticmethod
    def get_pakistan_jobs_for_digest(lookback_hours: int = 24) -> List[JobItemModel]:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=lookback_hours)).isoformat()
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM jobs
                WHERE fetched_at >= ?
                  AND city != 'Remote'
                  AND eligibility_status IN ('ELIGIBLE', 'MAYBE')
                ORDER BY
                  CASE WHEN eligibility_status = 'ELIGIBLE' THEN 0 ELSE 1 END,
                  relevance_score DESC
            """, (cutoff,))
            rows = cursor.fetchall()
            return [JobRepository._row_to_model(r) for r in rows]

    @staticmethod
    def get_remote_ai_jobs_for_digest(lookback_hours: int = 24) -> List[JobItemModel]:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=lookback_hours)).isoformat()
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM jobs
                WHERE fetched_at >= ?
                  AND city = 'Remote'
                  AND eligibility_status IN ('ELIGIBLE', 'MAYBE')
                ORDER BY
                  CASE WHEN eligibility_status = 'ELIGIBLE' THEN 0 ELSE 1 END,
                  relevance_score DESC
            """, (cutoff,))
            rows = cursor.fetchall()
            return [JobRepository._row_to_model(r) for r in rows]

    @staticmethod
    def get_closing_soon_jobs(days_window: int = 5) -> List[JobItemModel]:
        """Fetch open/saved eligible jobs whose deadline is approaching within days_window."""
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM jobs
                WHERE eligibility_status IN ('ELIGIBLE', 'MAYBE')
                  AND deadline != 'Not mentioned'
                  AND deadline != 'Open until filled'
                ORDER BY relevance_score DESC
                LIMIT 10
            """)
            rows = cursor.fetchall()
            return [JobRepository._row_to_model(r) for r in rows]

    @staticmethod
    def update_application_stage(job_id: int, stage: str, notes: Optional[str] = None) -> bool:
        now_str = datetime.now(timezone.utc).isoformat()
        with db_session() as conn:
            cursor = conn.cursor()
            if notes is not None:
                cursor.execute("""
                    UPDATE jobs SET application_stage = ?, notes = ?, application_date = ? WHERE id = ?
                """, (stage, notes, now_str, job_id))
            else:
                cursor.execute("""
                    UPDATE jobs SET application_stage = ?, application_date = ? WHERE id = ?
                """, (stage, now_str, job_id))
            return cursor.rowcount > 0

    @staticmethod
    def recalculate_all_eligibility(engine) -> int:
        """Recalculate eligibility for all stored jobs when profile updates."""
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs")
            rows = cursor.fetchall()
            updated_count = 0
            for r in rows:
                raw_job = RawJob(
                    title=r["title"],
                    organization=r["organization"],
                    city=r["city"],
                    url=r["primary_url"],
                    source_name="Stored",
                    description=f"{r['title']} {r['organization']} {r['required_qualification']} {r['required_experience']} {r['age_limit']}",
                    raw_qualification=r["required_qualification"],
                    raw_experience=r["required_experience"],
                    raw_age_limit=r["age_limit"],
                    raw_deadline=r["deadline"],
                    apply_link=r["apply_link"]
                )
                eval_res = engine.evaluate(raw_job)
                cursor.execute("""
                    UPDATE jobs SET
                        eligibility_status = ?,
                        eligibility_reason = ?,
                        relevance_score = ?
                    WHERE id = ?
                """, (eval_res.status, eval_res.reason, eval_res.relevance_score, r["id"]))
                updated_count += 1
            return updated_count

    @staticmethod
    def _row_to_model(r) -> JobItemModel:
        links = json.loads(r["source_links"]) if r["source_links"] else [r["primary_url"]]
        return JobItemModel(
            id=r["id"],
            title=r["title"],
            organization=r["organization"],
            city=r["city"],
            job_type=r["job_type"],
            required_qualification=r["required_qualification"],
            required_experience=r["required_experience"],
            age_limit=r["age_limit"],
            salary=r["salary"],
            deadline=r["deadline"],
            apply_link=r["apply_link"],
            source_links=links,
            primary_url=r["primary_url"],
            eligibility_status=r["eligibility_status"],
            eligibility_reason=r["eligibility_reason"],
            relevance_score=r["relevance_score"],
            application_stage=r["application_stage"],
            notes=r["notes"] or "",
            application_date=r["application_date"],
            fetched_at=r["fetched_at"],
            created_at=r["created_at"]
        )
