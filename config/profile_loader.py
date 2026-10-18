"""User profile loader and validator with dynamic age calculation."""
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
PROFILE_PATH = BASE_DIR / "profile.yaml"


class ExperienceYears(BaseModel):
    teaching: float = 3.0
    industry: float = 2.0
    placement_and_training: float = 2.0
    total: float = 4.0


class Locations(BaseModel):
    tier_1: List[str] = Field(default_factory=lambda: ["Lahore", "Gujranwala"])
    tier_2: List[str] = Field(default_factory=lambda: ["Sialkot", "Gujrat", "Islamabad"])
    tier_3: List[str] = Field(default_factory=lambda: ["Remote", "Hybrid"])


class ResearchInterests(BaseModel):
    primary: List[str] = Field(default_factory=list)
    topics_of_interest: List[str] = Field(default_factory=list)


class JobPreferences(BaseModel):
    target_roles: List[str] = Field(default_factory=list)
    organizations_of_interest: List[str] = Field(default_factory=list)


class UserProfile(BaseModel):
    personal: Dict[str, Any] = Field(default_factory=dict)
    education: Dict[str, Any] = Field(default_factory=dict)
    roles: List[str] = Field(default_factory=list)
    experience_years: ExperienceYears = Field(default_factory=ExperienceYears)
    locations: Locations = Field(default_factory=Locations)
    research_interests: ResearchInterests = Field(default_factory=ResearchInterests)
    job_preferences: JobPreferences = Field(default_factory=JobPreferences)

    @property
    def age(self) -> int:
        """Dynamically calculates current age each year based on birth_date."""
        birth_str = self.personal.get("birth_date")
        if birth_str:
            try:
                if isinstance(birth_str, (datetime, date)):
                    b_date = birth_str
                else:
                    b_date = datetime.strptime(str(birth_str).strip(), "%Y-%m-%d").date()
                today = date.today()
                calculated_age = today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
                return max(calculated_age, 18)
            except Exception:
                pass
        return int(self.personal.get("age", 28))

    @property
    def education_degree(self) -> str:
        return self.education.get("degree", "MS Computer Science")

    @property
    def education_level(self) -> str:
        return self.education.get("level", "MS/MPhil")

    @property
    def education_field(self) -> str:
        return self.education.get("field", "Computer Science")


def load_profile(path: Optional[Path] = None) -> UserProfile:
    file_path = path or PROFILE_PATH
    if not file_path.exists():
        return UserProfile()
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return UserProfile(**data)


def save_profile(profile_dict: Dict[str, Any], path: Optional[Path] = None) -> None:
    file_path = path or PROFILE_PATH
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(profile_dict, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
