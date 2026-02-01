"""
Profile Schema Migration Module
Converts legacy string-based profile fields to structured schema with normalized enums.

Schema Version:
- v1: Legacy string-based fields
- v2: Structured fields with raw, normalized, and metadata

Auto-fill engine should ONLY use normalized fields, with raw as fallback.
"""

from typing import Optional, List, Dict, Any
from enum import Enum
import re

# ========================
# ENUMS FOR NORMALIZED VALUES
# ========================

class WorkAuthorization(str, Enum):
    CITIZEN = "citizen"
    PERMANENT_RESIDENT = "permanent_resident"
    WORK_PERMIT = "work_permit"
    REQUIRE_SPONSORSHIP = "require_sponsorship"
    UNKNOWN = "unknown"

class SeniorityLevel(str, Enum):
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"
    DIRECTOR = "director"
    EXECUTIVE = "executive"
    UNKNOWN = "unknown"

class EducationLevel(str, Enum):
    HIGH_SCHOOL = "high_school"
    SOME_COLLEGE = "some_college"
    ASSOCIATE = "associate"
    BACHELOR = "bachelor"
    MASTER = "master"
    DOCTORATE = "doctorate"
    PROFESSIONAL = "professional"
    OTHER = "other"
    UNKNOWN = "unknown"

class WillingToRelocate(str, Enum):
    YES = "yes"
    NO = "no"
    OPEN_TO_DISCUSSION = "open_to_discussion"
    UNKNOWN = "unknown"

class NoticePeriod(str, Enum):
    IMMEDIATELY = "immediately"
    TWO_WEEKS = "two_weeks"
    ONE_MONTH = "one_month"
    TWO_MONTHS = "two_months"
    THREE_MONTHS_PLUS = "three_months_plus"
    UNKNOWN = "unknown"

class SkillYears(str, Enum):
    LESS_THAN_1 = "<1"
    ONE_TO_TWO = "1–2"
    THREE_TO_FIVE = "3–5"
    FIVE_PLUS = "5+"
    UNKNOWN = "unknown"

# ========================
# NORMALIZATION MAPPINGS
# ========================

WORK_AUTH_MAPPINGS = {
    # Citizen variations
    "citizen": WorkAuthorization.CITIZEN,
    "canadian_citizen": WorkAuthorization.CITIZEN,
    "us_citizen": WorkAuthorization.CITIZEN,
    "us citizen": WorkAuthorization.CITIZEN,
    "canadian citizen": WorkAuthorization.CITIZEN,
    "citizen/national": WorkAuthorization.CITIZEN,
    # Permanent resident variations
    "permanent_resident": WorkAuthorization.PERMANENT_RESIDENT,
    "permanent resident": WorkAuthorization.PERMANENT_RESIDENT,
    "pr": WorkAuthorization.PERMANENT_RESIDENT,
    "green card": WorkAuthorization.PERMANENT_RESIDENT,
    "green_card": WorkAuthorization.PERMANENT_RESIDENT,
    # Work permit variations
    "work_permit": WorkAuthorization.WORK_PERMIT,
    "work permit": WorkAuthorization.WORK_PERMIT,
    "work visa": WorkAuthorization.WORK_PERMIT,
    "h1b": WorkAuthorization.WORK_PERMIT,
    "h-1b": WorkAuthorization.WORK_PERMIT,
    "tn visa": WorkAuthorization.WORK_PERMIT,
    "ead": WorkAuthorization.WORK_PERMIT,
    # Sponsorship variations
    "require_sponsorship": WorkAuthorization.REQUIRE_SPONSORSHIP,
    "require sponsorship": WorkAuthorization.REQUIRE_SPONSORSHIP,
    "need sponsorship": WorkAuthorization.REQUIRE_SPONSORSHIP,
    "sponsorship required": WorkAuthorization.REQUIRE_SPONSORSHIP,
    "visa sponsorship": WorkAuthorization.REQUIRE_SPONSORSHIP,
}

SENIORITY_MAPPINGS = {
    "entry": SeniorityLevel.ENTRY,
    "entry level": SeniorityLevel.ENTRY,
    "entry-level": SeniorityLevel.ENTRY,
    "intern": SeniorityLevel.ENTRY,
    "junior": SeniorityLevel.JUNIOR,
    "jr": SeniorityLevel.JUNIOR,
    "associate": SeniorityLevel.JUNIOR,
    "mid": SeniorityLevel.MID,
    "mid-level": SeniorityLevel.MID,
    "mid level": SeniorityLevel.MID,
    "intermediate": SeniorityLevel.MID,
    "senior": SeniorityLevel.SENIOR,
    "sr": SeniorityLevel.SENIOR,
    "lead": SeniorityLevel.LEAD,
    "tech lead": SeniorityLevel.LEAD,
    "team lead": SeniorityLevel.LEAD,
    "principal": SeniorityLevel.LEAD,
    "manager": SeniorityLevel.MANAGER,
    "mgr": SeniorityLevel.MANAGER,
    "director": SeniorityLevel.DIRECTOR,
    "dir": SeniorityLevel.DIRECTOR,
    "vp": SeniorityLevel.EXECUTIVE,
    "vice president": SeniorityLevel.EXECUTIVE,
    "executive": SeniorityLevel.EXECUTIVE,
    "c-level": SeniorityLevel.EXECUTIVE,
    "cto": SeniorityLevel.EXECUTIVE,
    "ceo": SeniorityLevel.EXECUTIVE,
}

EDUCATION_MAPPINGS = {
    "high_school": EducationLevel.HIGH_SCHOOL,
    "high school": EducationLevel.HIGH_SCHOOL,
    "ged": EducationLevel.HIGH_SCHOOL,
    "some_college": EducationLevel.SOME_COLLEGE,
    "some college": EducationLevel.SOME_COLLEGE,
    "associate": EducationLevel.ASSOCIATE,
    "associates": EducationLevel.ASSOCIATE,
    "associate's": EducationLevel.ASSOCIATE,
    "aa": EducationLevel.ASSOCIATE,
    "as": EducationLevel.ASSOCIATE,
    "bachelor": EducationLevel.BACHELOR,
    "bachelors": EducationLevel.BACHELOR,
    "bachelor's": EducationLevel.BACHELOR,
    "ba": EducationLevel.BACHELOR,
    "bs": EducationLevel.BACHELOR,
    "bsc": EducationLevel.BACHELOR,
    "undergraduate": EducationLevel.BACHELOR,
    "master": EducationLevel.MASTER,
    "masters": EducationLevel.MASTER,
    "master's": EducationLevel.MASTER,
    "ma": EducationLevel.MASTER,
    "ms": EducationLevel.MASTER,
    "msc": EducationLevel.MASTER,
    "mba": EducationLevel.MASTER,
    "graduate": EducationLevel.MASTER,
    "doctorate": EducationLevel.DOCTORATE,
    "phd": EducationLevel.DOCTORATE,
    "ph.d": EducationLevel.DOCTORATE,
    "doctoral": EducationLevel.DOCTORATE,
    "md": EducationLevel.DOCTORATE,
    "jd": EducationLevel.DOCTORATE,
    "professional": EducationLevel.PROFESSIONAL,
    "certification": EducationLevel.PROFESSIONAL,
    "certificate": EducationLevel.PROFESSIONAL,
    "other": EducationLevel.OTHER,
}

RELOCATE_MAPPINGS = {
    "yes": WillingToRelocate.YES,
    "true": WillingToRelocate.YES,
    "willing": WillingToRelocate.YES,
    "no": WillingToRelocate.NO,
    "false": WillingToRelocate.NO,
    "not willing": WillingToRelocate.NO,
    "open_to_discussion": WillingToRelocate.OPEN_TO_DISCUSSION,
    "open to discussion": WillingToRelocate.OPEN_TO_DISCUSSION,
    "maybe": WillingToRelocate.OPEN_TO_DISCUSSION,
    "depends": WillingToRelocate.OPEN_TO_DISCUSSION,
}

NOTICE_MAPPINGS = {
    "immediately": NoticePeriod.IMMEDIATELY,
    "immediate": NoticePeriod.IMMEDIATELY,
    "available now": NoticePeriod.IMMEDIATELY,
    "now": NoticePeriod.IMMEDIATELY,
    "two_weeks": NoticePeriod.TWO_WEEKS,
    "two weeks": NoticePeriod.TWO_WEEKS,
    "2 weeks": NoticePeriod.TWO_WEEKS,
    "14 days": NoticePeriod.TWO_WEEKS,
    "one_month": NoticePeriod.ONE_MONTH,
    "one month": NoticePeriod.ONE_MONTH,
    "1 month": NoticePeriod.ONE_MONTH,
    "30 days": NoticePeriod.ONE_MONTH,
    "4 weeks": NoticePeriod.ONE_MONTH,
    "two_months": NoticePeriod.TWO_MONTHS,
    "two months": NoticePeriod.TWO_MONTHS,
    "2 months": NoticePeriod.TWO_MONTHS,
    "60 days": NoticePeriod.TWO_MONTHS,
    "three_months_plus": NoticePeriod.THREE_MONTHS_PLUS,
    "three months": NoticePeriod.THREE_MONTHS_PLUS,
    "3 months": NoticePeriod.THREE_MONTHS_PLUS,
    "3+ months": NoticePeriod.THREE_MONTHS_PLUS,
    "90 days": NoticePeriod.THREE_MONTHS_PLUS,
}

# Country code mappings for phone normalization
COUNTRY_PHONE_CODES = {
    "us": "+1",
    "usa": "+1",
    "united states": "+1",
    "ca": "+1",
    "canada": "+1",
    "uk": "+44",
    "united kingdom": "+44",
    "gb": "+44",
    "au": "+61",
    "australia": "+61",
    "in": "+91",
    "india": "+91",
    "de": "+49",
    "germany": "+49",
    "fr": "+33",
    "france": "+33",
}

# ========================
# STRUCTURED FIELD CLASSES
# ========================

def create_structured_field(raw: Any, normalized: Any, metadata: Dict = None) -> Dict:
    """Create a structured field with raw, normalized, and metadata."""
    return {
        "raw": raw,
        "normalized": normalized.value if hasattr(normalized, 'value') else normalized,
        "metadata": metadata or {}
    }

# ========================
# NORMALIZATION FUNCTIONS
# ========================

def normalize_work_authorization(raw: str) -> Dict:
    """Normalize work authorization string to structured field."""
    if not raw:
        return create_structured_field(None, WorkAuthorization.UNKNOWN)
    
    raw_lower = raw.lower().strip()
    normalized = WORK_AUTH_MAPPINGS.get(raw_lower, WorkAuthorization.UNKNOWN)
    
    return create_structured_field(raw, normalized)

def normalize_seniority(raw: str) -> Dict:
    """Normalize seniority level string to structured field."""
    if not raw:
        return create_structured_field(None, SeniorityLevel.UNKNOWN)
    
    raw_lower = raw.lower().strip()
    normalized = SENIORITY_MAPPINGS.get(raw_lower, SeniorityLevel.UNKNOWN)
    
    return create_structured_field(raw, normalized)

def normalize_education(raw: str) -> Dict:
    """Normalize education level string to structured field."""
    if not raw:
        return create_structured_field(None, EducationLevel.UNKNOWN)
    
    raw_lower = raw.lower().strip()
    normalized = EDUCATION_MAPPINGS.get(raw_lower, EducationLevel.UNKNOWN)
    
    return create_structured_field(raw, normalized)

def normalize_willing_to_relocate(raw: str) -> Dict:
    """Normalize willing to relocate string to structured field."""
    if not raw:
        return create_structured_field(None, WillingToRelocate.UNKNOWN)
    
    raw_lower = raw.lower().strip()
    normalized = RELOCATE_MAPPINGS.get(raw_lower, WillingToRelocate.UNKNOWN)
    
    return create_structured_field(raw, normalized)

def normalize_notice_period(raw: str) -> Dict:
    """Normalize notice period string to structured field."""
    if not raw:
        return create_structured_field(None, NoticePeriod.UNKNOWN)
    
    raw_lower = raw.lower().strip()
    normalized = NOTICE_MAPPINGS.get(raw_lower, NoticePeriod.UNKNOWN)
    
    return create_structured_field(raw, normalized)

def normalize_phone(raw: str, country: str = None) -> Dict:
    """Normalize phone number to structured field with country code."""
    if not raw:
        return create_structured_field(None, None, {"country_code": None})
    
    # Clean the phone number
    cleaned = re.sub(r'[^\d+]', '', raw)
    
    # Detect country code
    country_code = None
    if cleaned.startswith('+'):
        # Already has country code
        for code in ['+1', '+44', '+61', '+91', '+49', '+33']:
            if cleaned.startswith(code):
                country_code = code
                break
    elif country:
        country_code = COUNTRY_PHONE_CODES.get(country.lower(), "+1")
    else:
        country_code = "+1"  # Default to North America
    
    # Format normalized number
    digits_only = re.sub(r'[^\d]', '', raw)
    if len(digits_only) == 10:
        normalized = f"{country_code} ({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
    elif len(digits_only) == 11 and digits_only.startswith('1'):
        normalized = f"+1 ({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:]}"
    else:
        normalized = cleaned if cleaned.startswith('+') else f"{country_code}{cleaned}"
    
    return create_structured_field(raw, normalized, {"country_code": country_code})

def normalize_salary(min_val: int, max_val: int, currency: str = "USD") -> Dict:
    """Normalize salary to structured field with currency."""
    return {
        "raw": {"min": min_val, "max": max_val},
        "normalized": {
            "min": min_val,
            "max": max_val,
            "currency": currency.upper(),
            "period": "yearly"
        },
        "metadata": {
            "currency": currency.upper(),
            "period": "yearly"
        }
    }

def normalize_location(city: str, state: str, country: str) -> Dict:
    """Normalize location to structured field."""
    # Country code mapping
    country_codes = {
        "canada": "CA",
        "united states": "US",
        "usa": "US",
        "uk": "GB",
        "united kingdom": "GB",
        "australia": "AU",
        "germany": "DE",
        "france": "FR",
        "india": "IN",
    }
    
    country_code = country_codes.get(country.lower().strip(), country.upper()[:2]) if country else None
    
    return {
        "raw": {
            "city": city,
            "state": state,
            "country": country
        },
        "normalized": {
            "city": city.strip().title() if city else None,
            "state": state.strip() if state else None,
            "country_code": country_code
        },
        "metadata": {
            "country_full": country
        }
    }

def normalize_skill(skill: Any) -> Dict:
    """Normalize a single skill to structured field."""
    if isinstance(skill, str):
        return {
            "raw": skill,
            "normalized": {
                "name": skill.strip(),
                "years": None
            },
            "metadata": {}
        }
    elif isinstance(skill, dict):
        name = skill.get("name", "")
        years = skill.get("years")
        return {
            "raw": skill,
            "normalized": {
                "name": name.strip() if name else "",
                "years": years
            },
            "metadata": {}
        }
    return None

def normalize_skills(skills: List) -> List[Dict]:
    """Normalize skills list to structured fields."""
    if not skills:
        return []
    
    normalized = []
    for skill in skills:
        norm_skill = normalize_skill(skill)
        if norm_skill:
            normalized.append(norm_skill)
    
    return normalized

# ========================
# PROFILE MIGRATION
# ========================

def migrate_profile_to_v2(profile: Dict) -> Dict:
    """
    Migrate a v1 (string-based) profile to v2 (structured) format.
    This is backwards compatible - preserves all original fields.
    """
    if not profile:
        return profile
    
    # Check if already migrated
    if profile.get("profile_version") == 2:
        return profile
    
    # Create structured fields
    structured = {
        "profile_version": 2,
        
        # Preserve all original fields
        **profile,
        
        # Add structured versions
        "structured": {
            "work_authorization": normalize_work_authorization(profile.get("work_authorization")),
            "seniority_level": normalize_seniority(profile.get("seniority_level")),
            "highest_education": normalize_education(profile.get("highest_education")),
            "willing_to_relocate": normalize_willing_to_relocate(profile.get("willing_to_relocate")),
            "notice_period": normalize_notice_period(profile.get("notice_period")),
            "phone": normalize_phone(
                profile.get("phone_number"),
                profile.get("address_country")
            ),
            "salary": normalize_salary(
                profile.get("salary_min"),
                profile.get("salary_max"),
                "USD"  # Default currency
            ),
            "location": normalize_location(
                profile.get("address_city"),
                profile.get("address_state"),
                profile.get("address_country")
            ),
            "skills": normalize_skills(profile.get("skills", [])),
        }
    }
    
    return structured

def get_normalized_value(profile: Dict, field: str, subfield: str = None) -> Any:
    """
    Get the normalized value for auto-fill.
    Falls back to raw value if normalized is 'unknown' or None.
    """
    structured = profile.get("structured", {})
    field_data = structured.get(field, {})
    
    if not field_data:
        # Fall back to legacy field
        return profile.get(field)
    
    normalized = field_data.get("normalized")
    raw = field_data.get("raw")
    
    if subfield and isinstance(normalized, dict):
        norm_val = normalized.get(subfield)
        if norm_val and norm_val != "unknown":
            return norm_val
        # Fall back to raw
        if isinstance(raw, dict):
            return raw.get(subfield)
        return raw
    
    if normalized and normalized != "unknown":
        return normalized
    
    return raw

def get_autofill_data(profile: Dict) -> Dict:
    """
    Extract all normalized data for auto-fill purposes.
    Returns a flat dict optimized for form filling.
    """
    if profile.get("profile_version") != 2:
        profile = migrate_profile_to_v2(profile)
    
    structured = profile.get("structured", {})
    
    # Build autofill dict with normalized values
    autofill = {
        # Contact
        "first_name": profile.get("first_name", ""),
        "last_name": profile.get("last_name", ""),
        "full_name": profile.get("full_name", ""),
        "email": profile.get("email", ""),
        "phone": get_normalized_value(profile, "phone"),
        "phone_country_code": structured.get("phone", {}).get("metadata", {}).get("country_code"),
        
        # Location
        "city": get_normalized_value(profile, "location", "city"),
        "state": get_normalized_value(profile, "location", "state"),
        "country": get_normalized_value(profile, "location", "country_code"),
        
        # Professional
        "work_authorization": get_normalized_value(profile, "work_authorization"),
        "seniority_level": get_normalized_value(profile, "seniority_level"),
        "education": get_normalized_value(profile, "highest_education"),
        "willing_to_relocate": get_normalized_value(profile, "willing_to_relocate"),
        "notice_period": get_normalized_value(profile, "notice_period"),
        
        # Salary
        "salary_min": get_normalized_value(profile, "salary", "min"),
        "salary_max": get_normalized_value(profile, "salary", "max"),
        "salary_currency": structured.get("salary", {}).get("metadata", {}).get("currency", "USD"),
        
        # Links
        "linkedin_url": profile.get("linkedin_url", ""),
        "github_url": profile.get("github_url", ""),
        "portfolio_url": profile.get("portfolio_url", ""),
        
        # Other
        "current_company": profile.get("current_company", ""),
        "referral_source": profile.get("referral_source", ""),
        "experience_years": profile.get("experience_years", 0),
        
        # Skills (extract names only for simple matching)
        "skills": [s.get("normalized", {}).get("name", "") for s in structured.get("skills", []) if s],
        "skills_with_years": structured.get("skills", []),
    }
    
    return autofill
