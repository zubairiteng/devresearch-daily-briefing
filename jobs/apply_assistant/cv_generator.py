"""Job-specific ATS-friendly PDF CV generator using ReportLab."""
import re
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from database.models import JobItemModel
from .cv_parser import ParsedCVProfile

BASE_DIR = Path(__file__).resolve().parent.parent.parent
GENERATED_DIR = BASE_DIR / "private" / "generated"


def clean_filename_str(text: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", text)
    return "_".join(cleaned.strip().split())[:30]


def generate_tailored_pdf_cv(job: JobItemModel, cv: ParsedCVProfile) -> Path:
    """Compiles a tailored, truthful, single-page or two-page ATS-compliant PDF CV."""
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    safe_org = clean_filename_str(job.organization)
    safe_role = clean_filename_str(job.title)
    filename = f"CV_{safe_org}_{safe_role}.pdf"
    output_path = GENERATED_DIR / filename

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CVTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a")
    )
    contact_style = ParagraphStyle(
        "CVContact",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569")
    )
    heading_style = ParagraphStyle(
        "CVSectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=4,
        spaceBefore=8
    )
    role_style = ParagraphStyle(
        "CVRole",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor("#0f172a")
    )
    meta_style = ParagraphStyle(
        "CVMeta",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#64748b")
    )
    body_style = ParagraphStyle(
        "CVBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#334155")
    )

    story = []

    # 1. Header (Name & Contact)
    story.append(Paragraph(cv.name, title_style))
    contact_text = f"{cv.email} | {cv.phone} | {cv.location}"
    story.append(Paragraph(contact_text, contact_style))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=8))

    # Determine role orientation
    title_lower = job.title.lower()
    is_academic = any(k in title_lower for k in ["lecturer", "professor", "faculty", "research", "associate"])
    is_placement = any(k in title_lower for k in ["placement", "liaison", "career", "trainer", "navttc"])

    # 2. Executive Summary
    story.append(Paragraph("PROFESSIONAL SUMMARY", heading_style))
    if is_academic:
        summary_text = (
            f"MS Computer Science lecturer and active AI researcher with 3.5+ years of university teaching experience. "
            f"Passionate about computer science education, practical software laboratories, and publications in quantum computing and NLP."
        )
    elif is_placement:
        summary_text = (
            f"Experienced Placement Officer, Industry Liaison, and NAVTTC High-Tech Skills Coordinator with proven success "
            f"leading institutional recruitment drives, establishing employer partnerships, and structuring modern job-readiness curricula."
        )
    else:
        summary_text = (
            f"Full-Stack AI and Automation Engineer holding an MS in Computer Science, specializing in Large Language Model (LLM) agents, "
            f"Python workflow automation (n8n/Make/Zapier), and scalable FastAPI services."
        )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 4))

    # 3. Technical & Core Skills
    story.append(Paragraph("TECHNICAL & CORE COMPETENCIES", heading_style))
    skills_line = " &bull; ".join(cv.skills)
    story.append(Paragraph(skills_line, body_style))
    story.append(Spacer(1, 4))

    # 4. Work Experience (Prioritized)
    story.append(Paragraph("PROFESSIONAL EXPERIENCE", heading_style))
    for exp in cv.experience:
        story.append(Paragraph(f"<strong>{exp.get('role')}</strong> &mdash; {exp.get('organization')}", role_style))
        story.append(Paragraph(f"Duration: {exp.get('duration')}", meta_style))
        story.append(Paragraph(exp.get("details", ""), body_style))
        story.append(Spacer(1, 4))

    # 5. Teaching & Placement Highlights
    if is_academic or is_placement:
        story.append(Paragraph("TEACHING & TRAINING HIGHLIGHTS", heading_style))
        for t in cv.teaching:
            story.append(Paragraph(f"&bull; {t}", body_style))
        story.append(Spacer(1, 4))

    # 6. Education
    story.append(Paragraph("EDUCATION", heading_style))
    for edu in cv.education:
        story.append(Paragraph(f"<strong>{edu.get('degree')}</strong> &mdash; {edu.get('institution')} ({edu.get('year')})", role_style))
        if edu.get("details"):
            story.append(Paragraph(edu.get("details"), body_style))
        story.append(Spacer(1, 3))

    # 7. Research & Publications
    if cv.research_and_publications:
        story.append(Paragraph("RESEARCH & SCHOLARSHIP", heading_style))
        for r in cv.research_and_publications:
            story.append(Paragraph(f"&bull; {r}", body_style))

    doc.build(story)
    return output_path
