"""FastAPI REST API routes for DevResearch Daily Briefing dashboard."""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

from config import (
    settings, load_profile, save_profile, load_sources, save_sources,
    UserProfile, AppSources
)
from database.news_repo import NewsRepository
from database.models import NewsItemModel, JobItemModel, ResearchGapModel
from jobs.store.job_repo import JobRepository
from jobs.eligibility.engine import EligibilityEngine
from scheduler.runner import run_daily_briefing
from mailer.renderer import DigestRenderer
from mailer.sender import EmailSender

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


# Request/Response schemas
class ReadLaterToggleResponse(BaseModel):
    id: int
    read_later: bool


class JobStageUpdateRequest(BaseModel):
    stage: str
    notes: Optional[str] = None


class ProfileUpdateRequest(BaseModel):
    personal: Dict[str, Any]
    education: Dict[str, Any]
    roles: List[str]
    experience_years: Dict[str, float]
    locations: Dict[str, List[str]]
    research_interests: Dict[str, Any]
    job_preferences: Dict[str, Any]


class DeliverySettingsRequest(BaseModel):
    digest_time: str
    timezone: str
    mail_recipients: str
    mail_provider: str


@router.get("/digest/today")
async def get_today_digest():
    """Get categorized briefing items for Today tab."""
    all_news = NewsRepository.get_latest_news(limit=30)
    ai_items = [n for n in all_news if n.category == "ai_llm"]
    dev_items = [n for n in all_news if n.category == "software_cloud"]
    research_items = [n for n in all_news if n.category == "research_watch"]
    top_jobs = JobRepository.get_jobs_for_digest(lookback_hours=48)[:10]

    return {
        "date": datetime.now().strftime("%A, %B %d, %Y"),
        "counts": {
            "ai": len(ai_items),
            "dev": len(dev_items),
            "research": len(research_items),
            "jobs": len(top_jobs)
        },
        "ai_items": ai_items,
        "dev_items": dev_items,
        "research_items": research_items,
        "top_jobs": top_jobs
    }


@router.get("/digest/history")
async def get_history(
    q: Optional[str] = Query(None, description="Search keyword"),
    category: Optional[str] = Query(None, description="Category filter"),
    source: Optional[str] = Query(None, description="Source filter"),
    only_read_later: bool = Query(False, description="Only bookmarked"),
    limit: int = Query(60, le=200)
):
    items = NewsRepository.get_history(
        query=q,
        category=category,
        source=source,
        only_read_later=only_read_later,
        limit=limit
    )
    return {"count": len(items), "items": items}


@router.post("/news/{item_id}/read-later", response_model=ReadLaterToggleResponse)
async def toggle_read_later(item_id: int):
    new_state = NewsRepository.toggle_read_later(item_id)
    return ReadLaterToggleResponse(id=item_id, read_later=new_state)


@router.get("/research-gaps")
async def get_research_gaps():
    gaps = NewsRepository.get_research_gaps()
    return {"count": len(gaps), "gaps": gaps}


@router.get("/jobs")
async def get_jobs(
    city: Optional[str] = Query(None),
    eligibility_status: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    include_not_eligible: bool = Query(False),
    limit: int = Query(100, le=200)
):
    jobs = JobRepository.get_jobs(
        city=city,
        eligibility_status=eligibility_status,
        stage=stage,
        include_not_eligible=include_not_eligible,
        limit=limit
    )
    closing_soon = JobRepository.get_closing_soon_jobs(days_window=5)
    return {
        "count": len(jobs),
        "jobs": jobs,
        "closing_soon": closing_soon
    }


@router.post("/jobs/{job_id}/stage")
async def update_job_stage(job_id: int, req: JobStageUpdateRequest):
    success = JobRepository.update_application_stage(job_id, req.stage, req.notes)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"success": True, "job_id": job_id, "new_stage": req.stage}


@router.get("/settings")
async def get_settings():
    profile = load_profile()
    sources = load_sources()
    return {
        "profile": profile.model_dump(),
        "sources": sources.model_dump(),
        "delivery": {
            "digest_time": settings.DIGEST_TIME,
            "timezone": settings.TIMEZONE,
            "mail_recipients": settings.MAIL_RECIPIENTS,
            "mail_provider": settings.MAIL_PROVIDER,
            "llm_provider": settings.LLM_PROVIDER
        }
    }


@router.post("/settings/profile")
async def update_profile(req: ProfileUpdateRequest):
    """Update profile.yaml and automatically recalculate job eligibility!"""
    save_profile(req.model_dump())
    new_profile = load_profile()
    engine = EligibilityEngine(new_profile)
    recalculated_count = JobRepository.recalculate_all_eligibility(engine)
    logger.info(f"Profile updated and recalculated eligibility for {recalculated_count} stored jobs.")
    return {
        "success": True,
        "message": f"Profile saved successfully! Recalculated eligibility for {recalculated_count} jobs.",
        "calculated_age": new_profile.age
    }


@router.post("/settings/sources")
async def update_sources(sources_data: Dict[str, Any]):
    save_sources(sources_data)
    return {"success": True, "message": "Sources configuration saved successfully!"}


@router.post("/settings/delivery")
async def update_delivery_settings(req: DeliverySettingsRequest):
    # Update runtime settings and .env
    settings.DIGEST_TIME = req.digest_time
    settings.TIMEZONE = req.timezone
    settings.MAIL_RECIPIENTS = req.mail_recipients
    settings.MAIL_PROVIDER = req.mail_provider
    return {"success": True, "message": "Delivery settings updated!"}


@router.post("/pipeline/run")
async def trigger_pipeline_now(background_tasks: BackgroundTasks):
    """Run full briefing pipeline immediately."""
    background_tasks.add_task(run_daily_briefing)
    return {"success": True, "message": "Daily briefing pipeline triggered in background!"}


@router.post("/email/test")
async def send_test_email():
    """Send immediate test email using real database content."""
    renderer = DigestRenderer()
    sender = EmailSender()

    news_items = NewsRepository.get_latest_news(limit=15)
    jobs = JobRepository.get_jobs(include_not_eligible=False, limit=10)
    closing_soon = JobRepository.get_closing_soon_jobs(days_window=5)
    read_later = NewsRepository.get_history(only_read_later=True, limit=5)

    subject, html_body, txt_body = renderer.render_digest(
        news_items=news_items,
        jobs=jobs,
        closing_soon=closing_soon,
        read_later=read_later
    )
    subject = f"[TEST EMAIL] {subject}"

    success = sender.send_email(subject, html_body, txt_body)
    if not success:
        return {"success": False, "message": "Failed sending email. Check mail provider settings or server logs."}
    return {"success": True, "message": f"Test email sent to {settings.recipient_list} via {settings.MAIL_PROVIDER}!"}


# ==============================================================================
# Apply Assistant Routes
# ==============================================================================

@router.get("/apply/{job_id}/preview")
async def get_apply_preview(job_id: int):
    """Generates tailored cover letter, flags missing skills, and creates job-specific PDF CV."""
    from jobs.apply_assistant import get_current_cv_profile, generate_tailored_cover_letter, generate_tailored_pdf_cv

    # Find job
    all_jobs = JobRepository.get_jobs(include_not_eligible=True, limit=500)
    job = next((j for j in all_jobs if j.id == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    cv = get_current_cv_profile()
    cover_letter, matched, missing = generate_tailored_cover_letter(job, cv)
    cv_pdf_path = generate_tailored_pdf_cv(job, cv)

    is_email_apply = (job.apply_link or "").startswith("mailto:")
    apply_email = (job.apply_link or "").replace("mailto:", "") if is_email_apply else ""

    return {
        "job": job.model_dump(),
        "cover_letter": cover_letter,
        "matched_skills": matched,
        "missing_skills": missing,
        "cv_filename": cv_pdf_path.name,
        "download_url": f"/api/apply/download-cv/{cv_pdf_path.name}",
        "is_email_apply": is_email_apply,
        "apply_email": apply_email
    }


@router.post("/apply/{job_id}/browser-fill")
async def launch_browser_for_job(job_id: int, background_tasks: BackgroundTasks):
    """Launches Playwright visible desktop browser and pre-fills the application form."""
    from jobs.apply_assistant import get_current_cv_profile, generate_tailored_cover_letter, generate_tailored_pdf_cv, launch_browser_assist

    all_jobs = JobRepository.get_jobs(include_not_eligible=True, limit=500)
    job = next((j for j in all_jobs if j.id == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    cv = get_current_cv_profile()
    cover_letter, _, _ = generate_tailored_cover_letter(job, cv)
    cv_pdf_path = generate_tailored_pdf_cv(job, cv)

    # Launch browser in background task so API responds immediately
    background_tasks.add_task(launch_browser_assist, job, cv, cover_letter, cv_pdf_path)

    return {
        "success": True,
        "message": "Playwright visible browser launched on your desktop! Review fields and click Submit yourself."
    }


@router.post("/api/apply/{job_id}/send-email", include_in_schema=False)
@router.post("/apply/{job_id}/send-email")
async def send_application_email(job_id: int):
    """Sends email application with tailored cover letter and attached PDF CV."""
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.application import MIMEApplication
    from jobs.apply_assistant import get_current_cv_profile, generate_tailored_cover_letter, generate_tailored_pdf_cv

    all_jobs = JobRepository.get_jobs(include_not_eligible=True, limit=500)
    job = next((j for j in all_jobs if j.id == job_id), None)
    if not job or not (job.apply_link or "").startswith("mailto:"):
        raise HTTPException(status_code=400, detail="Job does not have a valid mailto apply link")

    target_email = job.apply_link.replace("mailto:", "").strip()
    cv = get_current_cv_profile()
    cover_letter, _, _ = generate_tailored_cover_letter(job, cv)
    cv_pdf_path = generate_tailored_pdf_cv(job, cv)

    subject = f"Application: {job.title} - {cv.name}"

    if settings.MAIL_PROVIDER == "console":
        print(f"[CONSOLE EMAIL APPLICATION DRAFT] To: {target_email} | Subject: {subject} | Attachment: {cv_pdf_path.name}")
        return {"success": True, "message": f"[Dev Mode] Application email drafted to {target_email} with CV attached!"}

    # SMTP dispatch
    try:
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = settings.MAIL_FROM
        msg["To"] = target_email
        msg.attach(MIMEText(cover_letter, "plain", "utf-8"))

        if cv_pdf_path.exists():
            with open(cv_pdf_path, "rb") as f:
                attach = MIMEApplication(f.read(), _subtype="pdf")
                attach.add_header("Content-Disposition", "attachment", filename=cv_pdf_path.name)
                msg.attach(attach)

        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20.0)
        if settings.SMTP_USE_TLS:
            server.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.MAIL_FROM, [target_email], msg.as_string())
        server.quit()
        return {"success": True, "message": f"Application email sent to {target_email} with {cv_pdf_path.name} attached!"}
    except Exception as e:
        logger.error(f"Failed sending application email: {e}")
        return {"success": False, "message": f"Error dispatching email: {str(e)}"}


@router.get("/apply/download-cv/{filename}")
async def download_cv(filename: str):
    from pathlib import Path
    from fastapi.responses import FileResponse
    file_path = Path(__file__).resolve().parent.parent / "private" / "generated" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="CV file not found")
    return FileResponse(str(file_path), media_type="application/pdf", filename=filename)

