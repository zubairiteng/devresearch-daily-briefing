"""Information extractor for Pakistani job advertisements."""
import re
from typing import Dict, Optional, Tuple


CITY_PATTERNS = [
    ("Gujranwala", r"\b(gujranwala)\b"),
    ("Lahore", r"\b(lahore)\b"),
    ("Sialkot", r"\b(sialkot)\b"),
    ("Gujrat", r"\b(gujrat)\b"),
    ("Islamabad", r"\b(islamabad|rawalpindi)\b"),
    ("Remote", r"\b(remote|work from home)\b"),
]

QUALIFICATION_PATTERNS = [
    ("PhD", r"\b(ph\.?d|doctorate)\b"),
    ("MS/MPhil", r"\b(ms|m\.phil|m\.s|master(?:'s)? in cs|master(?:'s)? in se|master(?:'s)? in it|18 years)\b"),
    ("BS/Bachelors", r"\b(bs|bsc|bachelor(?:'s)?|16 years of education)\b"),
    ("Diploma", r"\b(diploma|dae|intermediate)\b")
]


def extract_city(title: str, text: str, default: str = "Lahore") -> str:
    combined = f"{title} {text}".lower()
    for city, pattern in CITY_PATTERNS:
        if re.search(pattern, combined, re.IGNORECASE):
            return city
    return default


def extract_job_type(title: str, text: str) -> str:
    combined = f"{title} {text}".lower()
    if "visiting" in combined:
        return "Visiting Faculty"
    if "contract" in combined:
        return "Contract"
    if "permanent" in combined or "regular" in combined or "bps-" in combined:
        return "Permanent"
    if "fellowship" in combined or "scholarship" in combined:
        return "Fellowship/Scholarship"
    return "Full-Time"


def extract_qualification(text: str) -> str:
    text_lower = text.lower()
    for q_label, pattern in QUALIFICATION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            # Check context if mandatory or preferred
            if q_label == "PhD":
                if "phd required" in text_lower or "ph.d mandatory" in text_lower or "qualification: phd" in text_lower:
                    return "PhD mandatory"
                if "ms" in text_lower:
                    return "MS/MPhil (PhD preferred)"
                return "PhD"
            return q_label
    return "Not mentioned"


def extract_experience(text: str) -> Tuple[Optional[float], str]:
    """Extract required experience in years and human description."""
    text_clean = text.replace("\n", " ")

    # Explicit experience patterns: e.g. '3-5 years experience', 'minimum 2 years of experience', '2+ years'
    m = re.search(r"(?:min(?:imum)?|at least)?\s*(\d+(?:\.\d+)?)\s*(?:to|-)?\s*(\d+)?\s*\+?\s*years?\s+(?:of\s+)?(?:teaching|industry|research|placement|relevant|hands-on\s+)?experience", text_clean, re.IGNORECASE)
    if not m:
        # Check 'experience of 2-3 years' or 'experience: 2 years'
        m = re.search(r"experience\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\s*(?:to|-)?\s*(\d+)?\s*\+?\s*years?", text_clean, re.IGNORECASE)

    if m:
        min_exp = float(m.group(1))
        max_exp = float(m.group(2)) if m.group(2) else None
        if max_exp:
            desc = f"{int(min_exp)}-{int(max_exp)} years experience required"
        else:
            desc = f"{int(min_exp)} years experience required"
        return min_exp, desc

    if re.search(r"\b(fresh|no experience required|entry level)\b", text_clean, re.IGNORECASE):
        return 0.0, "Fresh / No prior experience required"

    return None, "Not mentioned"


def extract_age_limit(text: str) -> Tuple[Optional[int], Optional[int], str]:
    """Extract (min_age, max_age, description) from ad text."""
    text_clean = text.replace("\n", " ")

    # Range: e.g. '21 to 35 years', '25-35 years', 'age: 21-33 years'
    m_range = re.search(r"age(?:\s+limit)?\s*[:\-]?\s*(\d{2})\s*(?:to|-)\s*(\d{2})\s*years?", text_clean, re.IGNORECASE)
    if m_range:
        min_a = int(m_range.group(1))
        max_a = int(m_range.group(2))
        return min_a, max_a, f"{min_a}-{max_a} years"

    # Max age: e.g. 'maximum age 35', 'up to 35 years', 'upper age limit strictly 25 years', 'Max 25 years'
    m_max = re.search(r"(?:max(?:imum)?\s+age|up to|upper age limit|not exceeding|age limit)\s*(?:is|strictly)?\s*[:\-]?\s*(\d{2})\s*years?", text_clean, re.IGNORECASE)
    if not m_max:
        # Try standalone 'Max 25' or 'Max 35 years'
        m_max = re.search(r"\bmax(?:imum)?\s*(\d{2})\s*(?:years)?\b", text_clean, re.IGNORECASE)

    if m_max:
        max_a = int(m_max.group(1))
        if "relaxation" in text_clean.lower():
            return None, max_a, f"Max {max_a} years (general age relaxation applies)"
        return None, max_a, f"Max {max_a} years"

    return None, None, "Not mentioned"


def extract_deadline(text: str) -> str:
    """Extract application deadline date or return 'Not mentioned'."""
    text_clean = text.replace("\n", " ")
    patterns = [
        r"(?:last date|apply before|deadline|closing date)\s*[:\-]?\s*([A-Za-z0-9,\s\-]{6,25}(?:202[4-9]))",
        r"(\d{1,2}[-/.](?:\d{1,2}|[A-Za-z]{3})[-/.](?:202[4-9]|\d{2}))",
    ]
    for p in patterns:
        m = re.search(p, text_clean, re.IGNORECASE)
        if m:
            raw_val = m.group(1).strip()
            # Clean trailing words
            clean_val = re.split(r"(during|within|inclusive)", raw_val, flags=re.IGNORECASE)[0].strip()
            if len(clean_val) >= 6:
                return clean_val
    return "Not mentioned"


def extract_apply_channel(text: str, default_url: str) -> str:
    """Extract email apply address or default to provided URL."""
    email_match = re.search(r"\b([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\b", text)
    if email_match:
        return f"mailto:{email_match.group(1)}"
    return default_url
