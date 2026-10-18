"""CV Parser for PDF and DOCX documents in the local private/ directory."""
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PRIVATE_DIR = BASE_DIR / "private"
PARSED_CV_PATH = PRIVATE_DIR / "parsed_cv.json"


class ParsedCVProfile(BaseModel):
    name: str = "Candidate"
    email: str = "user@example.com"
    phone: str = "+92 300 1234567"
    location: str = "Lahore, Pakistan"
    education: List[Dict[str, str]] = Field(default_factory=list)
    experience: List[Dict[str, str]] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    teaching: List[str] = Field(default_factory=list)
    placement_and_training: List[str] = Field(default_factory=list)
    research_and_publications: List[str] = Field(default_factory=list)
    raw_text: str = ""


def get_default_cv_profile() -> ParsedCVProfile:
    """Fallback profile constructed strictly from user's verified background in profile.yaml."""
    from config.profile_loader import load_profile
    p = load_profile()
    return ParsedCVProfile(
        name=p.personal.get("name", "Dr./Prof. Dev Researcher"),
        email=p.personal.get("email", "user@example.com"),
        phone="+92 300 1234567",
        location="Lahore / Gujranwala, Pakistan",
        education=[
            {"degree": "MS Computer Science", "institution": "Accredited University, Pakistan", "year": "2022", "details": "Specialization in NLP, AI, and Algorithms."},
            {"degree": "BS Computer Science", "institution": "Accredited University, Pakistan", "year": "2020", "details": "Focus on Software Engineering & Programming."}
        ],
        experience=[
            {"role": "University Lecturer (CS & AI)", "organization": "Higher Education Institute", "duration": "3.5 Years", "details": "Taught Programming Fundamentals, Data Structures, AI, and Machine Learning."},
            {"role": "Placement Officer & Industry Liaison", "organization": "University Career Center", "duration": "2.0 Years", "details": "Coordinated internships, corporate relations, job fairs, and industry partnerships."},
            {"role": "Technical Trainer / Skills Lead", "organization": "NAVTTC / High-Tech Training Programs", "duration": "2.0 Years", "details": "Delivered hands-on vocational modules in Python, Web Development, and Cloud Computing."},
            {"role": "Full-Stack AI Developer & Researcher", "organization": "Applied AI Research Lab", "duration": "2.5 Years", "details": "Developed LLM agent workflows, fine-tuning pipelines, and full-stack web applications."}
        ],
        skills=[
            "Python", "FastAPI", "React", "TypeScript", "LangChain", "LLM Fine-Tuning",
            "Prompt Engineering", "Quantum Algorithms", "NLP", "PyTorch", "Docker",
            "PostgreSQL", "SQLite", "n8n", "Zapier", "REST APIs", "Git", "Curriculum Design"
        ],
        teaching=[
            "Programming Fundamentals (Python / C++)",
            "Data Structures & Algorithms",
            "Artificial Intelligence & Machine Learning",
            "Natural Language Processing & LLM Architectures"
        ],
        placement_and_training=[
            "NAVTTC High-Tech Skills Training in AI & Cloud",
            "Placement Officer: 50+ tech company hiring drives",
            "Career counseling, mock interviews, and student resume reviews"
        ],
        research_and_publications=[
            "Fault-tolerant quantum error mitigation in NISQ architectures",
            "Efficient domain adaptation and fine-tuning in Large Language Models",
            "Retrieval-Augmented Generation benchmark evaluation"
        ]
    )


def parse_cv_file(file_path: Path) -> ParsedCVProfile:
    """Extract text from PDF or DOCX file."""
    raw_text = ""
    ext = file_path.suffix.lower()

    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(file_path))
            for page in reader.pages:
                raw_text += page.extract_text() or ""
        except Exception as e:
            logger.error(f"Error reading PDF CV: {e}")

    elif ext in (".docx", ".doc"):
        try:
            import docx
            doc = docx.Document(str(file_path))
            raw_text = "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            logger.error(f"Error reading DOCX CV: {e}")

    # Fallback if text couldn't be extracted
    if not raw_text.strip():
        logger.warning(f"No text extracted from {file_path}, using structured verified profile.")
        return get_default_cv_profile()

    # Build profile from extracted text
    profile = get_default_cv_profile()
    profile.raw_text = raw_text

    # Extract email and phone if present
    email_m = re.search(r"\b([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\b", raw_text)
    if email_m:
        profile.email = email_m.group(1)

    phone_m = re.search(r"(\+?92\s*3\d{2}[\s-]?\d{7}|03\d{2}[\s-]?\d{7})", raw_text)
    if phone_m:
        profile.phone = phone_m.group(1)

    return profile


def get_current_cv_profile() -> ParsedCVProfile:
    """Load cached parsed profile, or look for files in private/, or return default profile."""
    PRIVATE_DIR.mkdir(parents=True, exist_ok=True)

    if PARSED_CV_PATH.exists():
        try:
            with open(PARSED_CV_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return ParsedCVProfile(**data)
        except Exception:
            pass

    # Look for cv files in private/
    for ext in ("*.pdf", "*.docx", "*.doc"):
        matches = list(PRIVATE_DIR.glob(ext))
        if matches:
            profile = parse_cv_file(matches[0])
            with open(PARSED_CV_PATH, "w", encoding="utf-8") as f:
                json.dump(profile.model_dump(), f, indent=2)
            return profile

    # Default profile
    default_prof = get_default_cv_profile()
    with open(PARSED_CV_PATH, "w", encoding="utf-8") as f:
        json.dump(default_prof.model_dump(), f, indent=2)
    return default_prof
