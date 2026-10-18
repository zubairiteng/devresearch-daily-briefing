"""Apply Assistant package."""
from .cv_parser import ParsedCVProfile, get_current_cv_profile, parse_cv_file
from .cover_letter import generate_tailored_cover_letter
from .cv_generator import generate_tailored_pdf_cv
from .browser_assist import launch_browser_assist

__all__ = [
    "ParsedCVProfile",
    "get_current_cv_profile",
    "parse_cv_file",
    "generate_tailored_cover_letter",
    "generate_tailored_pdf_cv",
    "launch_browser_assist",
]
