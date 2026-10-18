"""Job Eligibility Engine comparing jobs against the user profile."""
from dataclasses import dataclass
from typing import Optional, Tuple
from config.profile_loader import UserProfile
from jobs.fetchers.base_job_fetcher import RawJob
from jobs.parser.extractor import (
    extract_city, extract_job_type, extract_qualification,
    extract_experience, extract_age_limit, extract_deadline, extract_apply_channel
)


@dataclass
class EligibilityEvaluation:
    status: str  # "ELIGIBLE", "MAYBE", "NOT ELIGIBLE"
    reason: str
    relevance_score: int
    city: str
    job_type: str
    qualification: str
    experience_desc: str
    age_limit_desc: str
    deadline: str
    apply_link: str


class EligibilityEngine:
    def __init__(self, profile: UserProfile):
        self.profile = profile

    def evaluate(self, job: RawJob) -> EligibilityEvaluation:
        # 1. Parse fields if not already populated
        full_text = f"{job.title} {job.organization} {job.description}"
        city = job.city or extract_city(job.title, full_text, default="Lahore")
        job_type = job.job_type or extract_job_type(job.title, full_text)
        qualification = job.raw_qualification or extract_qualification(full_text)
        min_exp, exp_desc = extract_experience(full_text)
        if job.raw_experience:
            exp_desc = job.raw_experience
            r_min_e, _ = extract_experience(job.raw_experience)
            if r_min_e is not None:
                min_exp = r_min_e
        min_age, max_age, age_desc = extract_age_limit(full_text)
        if job.raw_age_limit:
            age_desc = job.raw_age_limit
            r_min_a, r_max_a, _ = extract_age_limit(job.raw_age_limit)
            if r_max_a is not None:
                max_age = r_max_a
            if r_min_a is not None:
                min_age = r_min_a
        deadline = job.raw_deadline or extract_deadline(full_text)
        apply_link = job.apply_link or extract_apply_channel(full_text, job.url)

        user_age = self.profile.age
        user_qual = self.profile.education_level  # "MS/MPhil"
        teaching_exp = self.profile.experience_years.teaching
        industry_exp = self.profile.experience_years.industry
        placement_exp = self.profile.experience_years.placement_and_training
        total_exp = self.profile.experience_years.total

        # Determine user applicable experience depending on role
        title_lower = job.title.lower()
        if "lecturer" in title_lower or "faculty" in title_lower or "teacher" in title_lower:
            relevant_user_exp = teaching_exp
            role_type = "teaching"
        elif "placement" in title_lower or "counselor" in title_lower or "liaison" in title_lower or "navttc" in title_lower:
            relevant_user_exp = placement_exp
            role_type = "placement/training"
        else:
            relevant_user_exp = total_exp
            role_type = "tech/industry"

        # 2. Hard Eligibility Checks
        reasons = []
        is_not_eligible = False
        is_maybe = False

        # --- A. Age Check ---
        if max_age is not None:
            if user_age > max_age:
                reasons.append(f"Max age {max_age}, you are {user_age}: Exceeds limit")
                is_not_eligible = True
            elif min_age and user_age < min_age:
                reasons.append(f"Min age {min_age}, you are {user_age}: Under limit")
                is_not_eligible = True
            else:
                reasons.append(f"Max age {max_age}, you are {user_age}: OK")
        else:
            reasons.append("Age limit: Not mentioned")
            is_maybe = True

        # --- B. Qualification Check ---
        if "phd mandatory" in qualification.lower():
            reasons.append(f"PhD mandatory required, you have {user_qual}: Not eligible")
            is_not_eligible = True
        elif "phd" in qualification.lower() and "preferred" in qualification.lower():
            reasons.append(f"MS required (PhD preferred), you have {user_qual}: OK")
        elif "ms" in qualification.lower() or "mphil" in qualification.lower() or "master" in qualification.lower():
            reasons.append(f"MS/MPhil required, you have {user_qual}: OK")
        elif "bs" in qualification.lower() or "bachelor" in qualification.lower():
            reasons.append(f"BS/16 years required, you have {user_qual}: Exceeds/OK")
        elif qualification == "Not mentioned":
            reasons.append("Qualification: Not mentioned")
            is_maybe = True
        else:
            reasons.append(f"Qualification: {qualification}")
            is_maybe = True

        # --- C. Experience Check ---
        if min_exp is not None:
            if relevant_user_exp < min_exp:
                reasons.append(f"{min_exp} yrs {role_type} required, you have {relevant_user_exp} yrs: Insufficient")
                is_not_eligible = True
            else:
                reasons.append(f"{min_exp} yrs required, you have {relevant_user_exp} yrs: OK")
        elif "fresh" in exp_desc.lower():
            reasons.append("Fresh graduates eligible: OK")
        else:
            reasons.append("Experience: Not mentioned")
            is_maybe = True

        # --- D. Remote & Country Restrictions Check ---
        is_remote_job = (city.lower() == "remote" or "remote" in job.title.lower() or "remote" in job.description.lower())
        if is_remote_job:
            from jobs.fetchers.remote_fetcher import detect_pakistan_eligibility
            pk_allowed, pk_reason = detect_pakistan_eligibility(city, full_text)
            reasons.append(pk_reason)
            if not pk_allowed:
                is_not_eligible = True

        # 3. Determine Overall Status
        if is_not_eligible:
            final_status = "NOT ELIGIBLE"
        elif is_maybe:
            final_status = "MAYBE"
        else:
            final_status = "ELIGIBLE"

        one_line_reason = ". ".join(reasons) + "."

        # 4. Compute Relevance Score (0-100)
        score = 30  # Baseline

        # Location priority:
        # Tier 1: Lahore, Gujranwala -> +35
        # Tier 2: Sialkot, Gujrat, Islamabad -> +20
        # Tier 3: Remote -> +20 (with Pakistan-friendly boost)
        if city in self.profile.locations.tier_1:
            score += 35
        elif city in self.profile.locations.tier_2:
            score += 20
        elif is_remote_job:
            score += 20
            if "Open to applicants from Pakistan" in one_line_reason or "Open to Pakistan" in one_line_reason:
                score += 10

        # AI & Automation role match
        ai_automation_kws = ["automation", "agent", "llm", "generative ai", "genai", "prompt", "rpa", "n8n", "zapier", "make", "nlp", "mlops", "data science", "machine learning"]
        if any(kw in title_lower for kw in ai_automation_kws):
            score += 25
            score += 20
        elif "remote" in city.lower() or "remote" in self.profile.locations.tier_3:
            score += 15

        # Target Role match -> +25
        target_roles = [r.lower() for r in self.profile.job_preferences.target_roles]
        if any(tr in title_lower for tr in target_roles):
            score += 25

        # Subject / Tech match (CS, AI, Programming, Data Science) -> +15
        if any(sub in full_text.lower() for sub in ["computer science", "ai", "artificial intelligence", "software", "programming"]):
            score += 15

        # Target organization bonus -> +10
        target_orgs = [o.lower() for o in self.profile.job_preferences.organizations_of_interest]
        if any(to in full_text.lower() for to in target_orgs):
            score += 10

        # Eligibility boost / penalty
        if final_status == "ELIGIBLE":
            score += 10
        elif final_status == "NOT ELIGIBLE":
            score -= 20

        final_relevance = max(10, min(100, score))

        return EligibilityEvaluation(
            status=final_status,
            reason=one_line_reason,
            relevance_score=final_relevance,
            city=city,
            job_type=job_type,
            qualification=qualification,
            experience_desc=exp_desc,
            age_limit_desc=age_desc,
            deadline=deadline,
            apply_link=apply_link
        )
