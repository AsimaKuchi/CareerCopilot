"""
Profile Schema Migration Module v2
Converts legacy string-based profile fields to structured schema with normalized enums.

Schema Version:
- v1: Legacy string-based fields
- v2: Structured fields with raw, normalized, and metadata

Auto-fill engine should ONLY use normalized fields, with raw as fallback.
"""

from typing import Optional, List, Dict, Any, Union
from enum import Enum
from datetime import datetime, timezone
import re

# ========================
# ENUMS FOR NORMALIZED VALUES
# ========================

class WorkAuthorizationStatus(str, Enum):
    # Universal
    CITIZEN = "citizen"
    PERMANENT_RESIDENT = "permanent_resident"
    NOT_AUTHORIZED = "not_authorized"
    
    # Canada specific
    OPEN_WORK_PERMIT = "open_work_permit"
    PGWP = "pgwp"  # Post-Graduation Work Permit
    EMPLOYER_SPECIFIC_WORK_PERMIT = "employer_specific_work_permit"
    STUDENT = "student"
    
    # US specific
    GREEN_CARD = "green_card"
    H1B = "h1b"
    L1 = "l1"
    TN = "tn"
    OPT = "opt"
    CPT = "cpt"
    EAD = "ead"
    
    # Generic
    WORK_PERMIT = "work_permit"
    REQUIRE_SPONSORSHIP = "require_sponsorship"
    UNKNOWN = "unknown"

class SeniorityLevel(str, Enum):
    INTERN = "intern"
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    STAFF = "staff"
    PRINCIPAL = "principal"
    LEAD = "lead"
    MANAGER = "manager"
    SENIOR_MANAGER = "senior_manager"
    DIRECTOR = "director"
    VP = "vp"
    SVP = "svp"
    C_LEVEL = "c_level"
    UNKNOWN = "unknown"

class EducationLevel(str, Enum):
    NONE = "none"
    HIGH_SCHOOL = "high_school"
    SOME_COLLEGE = "some_college"
    ASSOCIATE = "associate"
    BACHELOR = "bachelor"
    MASTER = "master"
    DOCTORATE = "doctorate"
    PROFESSIONAL = "professional"  # MD, JD, etc.
    BOOTCAMP = "bootcamp"
    CERTIFICATION = "certification"
    OTHER = "other"
    UNKNOWN = "unknown"

class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    UNKNOWN = "unknown"

class WorkArrangement(str, Enum):
    ONSITE = "onsite"
    REMOTE = "remote"
    HYBRID = "hybrid"
    FLEXIBLE = "flexible"
    UNKNOWN = "unknown"

class JobType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    TEMPORARY = "temporary"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"
    UNKNOWN = "unknown"

class WillingToRelocate(str, Enum):
    YES = "yes"
    NO = "no"
    OPEN_TO_DISCUSSION = "open_to_discussion"
    UNKNOWN = "unknown"

class NoticePeriod(str, Enum):
    IMMEDIATELY = "immediately"
    ONE_WEEK = "one_week"
    TWO_WEEKS = "two_weeks"
    THREE_WEEKS = "three_weeks"
    ONE_MONTH = "one_month"
    SIX_WEEKS = "six_weeks"
    TWO_MONTHS = "two_months"
    THREE_MONTHS = "three_months"
    THREE_MONTHS_PLUS = "three_months_plus"
    UNKNOWN = "unknown"

# ========================
# NORMALIZATION MAPPINGS
# ========================

WORK_AUTH_MAPPINGS = {
    # Citizen variations
    "citizen": WorkAuthorizationStatus.CITIZEN,
    "canadian_citizen": WorkAuthorizationStatus.CITIZEN,
    "us_citizen": WorkAuthorizationStatus.CITIZEN,
    "us citizen": WorkAuthorizationStatus.CITIZEN,
    "canadian citizen": WorkAuthorizationStatus.CITIZEN,
    "citizen/national": WorkAuthorizationStatus.CITIZEN,
    
    # Permanent resident variations
    "permanent_resident": WorkAuthorizationStatus.PERMANENT_RESIDENT,
    "permanent resident": WorkAuthorizationStatus.PERMANENT_RESIDENT,
    "pr": WorkAuthorizationStatus.PERMANENT_RESIDENT,
    "green card": WorkAuthorizationStatus.GREEN_CARD,
    "green_card": WorkAuthorizationStatus.GREEN_CARD,
    "greencard": WorkAuthorizationStatus.GREEN_CARD,
    
    # Canada work permits
    "open_work_permit": WorkAuthorizationStatus.OPEN_WORK_PERMIT,
    "open work permit": WorkAuthorizationStatus.OPEN_WORK_PERMIT,
    "owp": WorkAuthorizationStatus.OPEN_WORK_PERMIT,
    "pgwp": WorkAuthorizationStatus.PGWP,
    "post-graduation work permit": WorkAuthorizationStatus.PGWP,
    "post graduation work permit": WorkAuthorizationStatus.PGWP,
    "employer_specific_work_permit": WorkAuthorizationStatus.EMPLOYER_SPECIFIC_WORK_PERMIT,
    "employer specific work permit": WorkAuthorizationStatus.EMPLOYER_SPECIFIC_WORK_PERMIT,
    "lmia": WorkAuthorizationStatus.EMPLOYER_SPECIFIC_WORK_PERMIT,
    "student": WorkAuthorizationStatus.STUDENT,
    "study permit": WorkAuthorizationStatus.STUDENT,
    "international student": WorkAuthorizationStatus.STUDENT,
    
    # US work permits
    "h1b": WorkAuthorizationStatus.H1B,
    "h-1b": WorkAuthorizationStatus.H1B,
    "h1-b": WorkAuthorizationStatus.H1B,
    "l1": WorkAuthorizationStatus.L1,
    "l-1": WorkAuthorizationStatus.L1,
    "tn": WorkAuthorizationStatus.TN,
    "tn visa": WorkAuthorizationStatus.TN,
    "opt": WorkAuthorizationStatus.OPT,
    "cpt": WorkAuthorizationStatus.CPT,
    "ead": WorkAuthorizationStatus.EAD,
    
    # Generic work permit
    "work_permit": WorkAuthorizationStatus.WORK_PERMIT,
    "work permit": WorkAuthorizationStatus.WORK_PERMIT,
    "work visa": WorkAuthorizationStatus.WORK_PERMIT,
    
    # Sponsorship
    "require_sponsorship": WorkAuthorizationStatus.REQUIRE_SPONSORSHIP,
    "require sponsorship": WorkAuthorizationStatus.REQUIRE_SPONSORSHIP,
    "need sponsorship": WorkAuthorizationStatus.REQUIRE_SPONSORSHIP,
    "sponsorship required": WorkAuthorizationStatus.REQUIRE_SPONSORSHIP,
    "visa sponsorship": WorkAuthorizationStatus.REQUIRE_SPONSORSHIP,
    
    # Not authorized
    "not_authorized": WorkAuthorizationStatus.NOT_AUTHORIZED,
    "not authorized": WorkAuthorizationStatus.NOT_AUTHORIZED,
    "no authorization": WorkAuthorizationStatus.NOT_AUTHORIZED,
}

SENIORITY_MAPPINGS = {
    "intern": SeniorityLevel.INTERN,
    "internship": SeniorityLevel.INTERN,
    "entry": SeniorityLevel.ENTRY,
    "entry level": SeniorityLevel.ENTRY,
    "entry-level": SeniorityLevel.ENTRY,
    "junior": SeniorityLevel.JUNIOR,
    "jr": SeniorityLevel.JUNIOR,
    "associate": SeniorityLevel.JUNIOR,
    "mid": SeniorityLevel.MID,
    "mid-level": SeniorityLevel.MID,
    "mid level": SeniorityLevel.MID,
    "intermediate": SeniorityLevel.MID,
    "senior": SeniorityLevel.SENIOR,
    "sr": SeniorityLevel.SENIOR,
    "staff": SeniorityLevel.STAFF,
    "staff engineer": SeniorityLevel.STAFF,
    "principal": SeniorityLevel.PRINCIPAL,
    "lead": SeniorityLevel.LEAD,
    "tech lead": SeniorityLevel.LEAD,
    "team lead": SeniorityLevel.LEAD,
    "manager": SeniorityLevel.MANAGER,
    "mgr": SeniorityLevel.MANAGER,
    "engineering manager": SeniorityLevel.MANAGER,
    "senior_manager": SeniorityLevel.SENIOR_MANAGER,
    "senior manager": SeniorityLevel.SENIOR_MANAGER,
    "director": SeniorityLevel.DIRECTOR,
    "dir": SeniorityLevel.DIRECTOR,
    "vp": SeniorityLevel.VP,
    "vice president": SeniorityLevel.VP,
    "svp": SeniorityLevel.SVP,
    "senior vice president": SeniorityLevel.SVP,
    "c_level": SeniorityLevel.C_LEVEL,
    "c-level": SeniorityLevel.C_LEVEL,
    "executive": SeniorityLevel.C_LEVEL,
    "cto": SeniorityLevel.C_LEVEL,
    "ceo": SeniorityLevel.C_LEVEL,
    "cfo": SeniorityLevel.C_LEVEL,
    "coo": SeniorityLevel.C_LEVEL,
}

EDUCATION_MAPPINGS = {
    "none": EducationLevel.NONE,
    "no degree": EducationLevel.NONE,
    "high_school": EducationLevel.HIGH_SCHOOL,
    "high school": EducationLevel.HIGH_SCHOOL,
    "ged": EducationLevel.HIGH_SCHOOL,
    "secondary": EducationLevel.HIGH_SCHOOL,
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
    "beng": EducationLevel.BACHELOR,
    "undergraduate": EducationLevel.BACHELOR,
    "master": EducationLevel.MASTER,
    "masters": EducationLevel.MASTER,
    "master's": EducationLevel.MASTER,
    "ma": EducationLevel.MASTER,
    "ms": EducationLevel.MASTER,
    "msc": EducationLevel.MASTER,
    "mba": EducationLevel.MASTER,
    "meng": EducationLevel.MASTER,
    "graduate": EducationLevel.MASTER,
    "doctorate": EducationLevel.DOCTORATE,
    "phd": EducationLevel.DOCTORATE,
    "ph.d": EducationLevel.DOCTORATE,
    "ph.d.": EducationLevel.DOCTORATE,
    "doctoral": EducationLevel.DOCTORATE,
    "professional": EducationLevel.PROFESSIONAL,
    "md": EducationLevel.PROFESSIONAL,
    "jd": EducationLevel.PROFESSIONAL,
    "bootcamp": EducationLevel.BOOTCAMP,
    "coding bootcamp": EducationLevel.BOOTCAMP,
    "certification": EducationLevel.CERTIFICATION,
    "certificate": EducationLevel.CERTIFICATION,
    "other": EducationLevel.OTHER,
}

WORK_ARRANGEMENT_MAPPINGS = {
    "onsite": WorkArrangement.ONSITE,
    "on-site": WorkArrangement.ONSITE,
    "on site": WorkArrangement.ONSITE,
    "office": WorkArrangement.ONSITE,
    "in-office": WorkArrangement.ONSITE,
    "remote": WorkArrangement.REMOTE,
    "work from home": WorkArrangement.REMOTE,
    "wfh": WorkArrangement.REMOTE,
    "hybrid": WorkArrangement.HYBRID,
    "flexible": WorkArrangement.FLEXIBLE,
}

JOB_TYPE_MAPPINGS = {
    "full_time": JobType.FULL_TIME,
    "full-time": JobType.FULL_TIME,
    "full time": JobType.FULL_TIME,
    "fulltime": JobType.FULL_TIME,
    "ft": JobType.FULL_TIME,
    "part_time": JobType.PART_TIME,
    "part-time": JobType.PART_TIME,
    "part time": JobType.PART_TIME,
    "parttime": JobType.PART_TIME,
    "pt": JobType.PART_TIME,
    "contract": JobType.CONTRACT,
    "contractor": JobType.CONTRACT,
    "c2c": JobType.CONTRACT,
    "temporary": JobType.TEMPORARY,
    "temp": JobType.TEMPORARY,
    "internship": JobType.INTERNSHIP,
    "intern": JobType.INTERNSHIP,
    "freelance": JobType.FREELANCE,
    "freelancer": JobType.FREELANCE,
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
    "asap": NoticePeriod.IMMEDIATELY,
    "one_week": NoticePeriod.ONE_WEEK,
    "one week": NoticePeriod.ONE_WEEK,
    "1 week": NoticePeriod.ONE_WEEK,
    "7 days": NoticePeriod.ONE_WEEK,
    "two_weeks": NoticePeriod.TWO_WEEKS,
    "two weeks": NoticePeriod.TWO_WEEKS,
    "2 weeks": NoticePeriod.TWO_WEEKS,
    "14 days": NoticePeriod.TWO_WEEKS,
    "three_weeks": NoticePeriod.THREE_WEEKS,
    "three weeks": NoticePeriod.THREE_WEEKS,
    "3 weeks": NoticePeriod.THREE_WEEKS,
    "one_month": NoticePeriod.ONE_MONTH,
    "one month": NoticePeriod.ONE_MONTH,
    "1 month": NoticePeriod.ONE_MONTH,
    "30 days": NoticePeriod.ONE_MONTH,
    "4 weeks": NoticePeriod.ONE_MONTH,
    "six_weeks": NoticePeriod.SIX_WEEKS,
    "six weeks": NoticePeriod.SIX_WEEKS,
    "6 weeks": NoticePeriod.SIX_WEEKS,
    "two_months": NoticePeriod.TWO_MONTHS,
    "two months": NoticePeriod.TWO_MONTHS,
    "2 months": NoticePeriod.TWO_MONTHS,
    "60 days": NoticePeriod.TWO_MONTHS,
    "8 weeks": NoticePeriod.TWO_MONTHS,
    "three_months": NoticePeriod.THREE_MONTHS,
    "three months": NoticePeriod.THREE_MONTHS,
    "3 months": NoticePeriod.THREE_MONTHS,
    "90 days": NoticePeriod.THREE_MONTHS,
    "three_months_plus": NoticePeriod.THREE_MONTHS_PLUS,
    "3+ months": NoticePeriod.THREE_MONTHS_PLUS,
    "more than 3 months": NoticePeriod.THREE_MONTHS_PLUS,
}

# Country phone codes
COUNTRY_PHONE_CODES = {
    "us": "+1", "usa": "+1", "united states": "+1",
    "ca": "+1", "canada": "+1",
    "uk": "+44", "united kingdom": "+44", "gb": "+44",
    "au": "+61", "australia": "+61",
    "in": "+91", "india": "+91",
    "de": "+49", "germany": "+49",
    "fr": "+33", "france": "+33",
    "jp": "+81", "japan": "+81",
    "cn": "+86", "china": "+86",
    "br": "+55", "brazil": "+55",
    "mx": "+52", "mexico": "+52",
}

# Country code mappings
COUNTRY_CODES = {
    "canada": "CA", "united states": "US", "usa": "US",
    "uk": "GB", "united kingdom": "GB", "australia": "AU",
    "germany": "DE", "france": "FR", "india": "IN",
    "japan": "JP", "china": "CN", "brazil": "BR", "mexico": "MX",
}

# ========================
# SKILL YEARS BUCKET MAPPING
# ========================

def years_to_bucket(years: Union[int, float, None]) -> str:
    """Convert numeric years to display bucket."""
    if years is None:
        return None
    if years < 1:
        return "<1"
    elif years < 3:
        return "1-2"
    elif years < 6:
        return "3-5"
    else:
        return "5+"

def bucket_to_years(bucket: str) -> int:
    """Convert bucket string to approximate numeric years (midpoint)."""
    if not bucket:
        return None
    bucket = bucket.strip()
    if bucket == "<1":
        return 0.5
    elif bucket in ["1-2", "1–2"]:
        return 1.5
    elif bucket in ["3-5", "3–5"]:
        return 4
    elif bucket in ["5+", "5+"]:
        return 7
    else:
        # Try to parse as number
        try:
            return float(bucket)
        except:
            return None

# ========================
# NORMALIZATION FUNCTIONS
# ========================

def normalize_work_authorization(raw: str, country: str = None) -> Dict:
    """
    Normalize work authorization to structured field.
    Returns: { country, status, requiresSponsorship, expiryDate }
    """
    if not raw:
        return {
            "raw": None,
            "normalized": {
                "country": country or "CA",
                "status": WorkAuthorizationStatus.UNKNOWN.value,
                "requiresSponsorship": None,
                "expiryDate": None
            },
            "metadata": {}
        }
    
    raw_lower = raw.lower().strip()
    status = WORK_AUTH_MAPPINGS.get(raw_lower, WorkAuthorizationStatus.UNKNOWN)
    
    # Determine if sponsorship is required
    requires_sponsorship = None
    if status in [WorkAuthorizationStatus.CITIZEN, WorkAuthorizationStatus.PERMANENT_RESIDENT, 
                  WorkAuthorizationStatus.GREEN_CARD]:
        requires_sponsorship = False
    elif status in [WorkAuthorizationStatus.REQUIRE_SPONSORSHIP, WorkAuthorizationStatus.STUDENT,
                    WorkAuthorizationStatus.NOT_AUTHORIZED]:
        requires_sponsorship = True
    elif status in [WorkAuthorizationStatus.H1B, WorkAuthorizationStatus.L1, WorkAuthorizationStatus.TN,
                    WorkAuthorizationStatus.OPT, WorkAuthorizationStatus.CPT, WorkAuthorizationStatus.EAD,
                    WorkAuthorizationStatus.PGWP, WorkAuthorizationStatus.OPEN_WORK_PERMIT,
                    WorkAuthorizationStatus.EMPLOYER_SPECIFIC_WORK_PERMIT]:
        requires_sponsorship = True  # Will need sponsorship for future visa
    
    # Infer country from status
    inferred_country = country
    if not inferred_country:
        if status in [WorkAuthorizationStatus.PGWP, WorkAuthorizationStatus.OPEN_WORK_PERMIT,
                      WorkAuthorizationStatus.EMPLOYER_SPECIFIC_WORK_PERMIT]:
            inferred_country = "CA"
        elif status in [WorkAuthorizationStatus.H1B, WorkAuthorizationStatus.L1, 
                        WorkAuthorizationStatus.OPT, WorkAuthorizationStatus.CPT,
                        WorkAuthorizationStatus.GREEN_CARD, WorkAuthorizationStatus.EAD]:
            inferred_country = "US"
        elif "canadian" in raw_lower:
            inferred_country = "CA"
        elif "us" in raw_lower or "american" in raw_lower:
            inferred_country = "US"
        else:
            inferred_country = "CA"  # Default
    
    return {
        "raw": raw,
        "normalized": {
            "country": inferred_country,
            "status": status.value,
            "requiresSponsorship": requires_sponsorship,
            "expiryDate": None
        },
        "metadata": {}
    }

def normalize_seniority(raw: str) -> Dict:
    """Normalize seniority level string to structured field."""
    if not raw:
        return {
            "raw": None,
            "normalized": SeniorityLevel.UNKNOWN.value,
            "metadata": {}
        }
    
    raw_lower = raw.lower().strip()
    normalized = SENIORITY_MAPPINGS.get(raw_lower, SeniorityLevel.UNKNOWN)
    
    return {
        "raw": raw,
        "normalized": normalized.value,
        "metadata": {}
    }

def normalize_education(raw: str) -> Dict:
    """Normalize education level string to structured field."""
    if not raw:
        return {
            "raw": None,
            "normalized": EducationLevel.UNKNOWN.value,
            "metadata": {}
        }
    
    raw_lower = raw.lower().strip()
    normalized = EDUCATION_MAPPINGS.get(raw_lower, EducationLevel.UNKNOWN)
    
    return {
        "raw": raw,
        "normalized": normalized.value,
        "metadata": {}
    }

def normalize_willing_to_relocate(raw: str) -> Dict:
    """Normalize willing to relocate string to structured field."""
    if not raw:
        return {
            "raw": None,
            "normalized": WillingToRelocate.UNKNOWN.value,
            "metadata": {}
        }
    
    raw_lower = raw.lower().strip()
    normalized = RELOCATE_MAPPINGS.get(raw_lower, WillingToRelocate.UNKNOWN)
    
    return {
        "raw": raw,
        "normalized": normalized.value,
        "metadata": {}
    }

def normalize_notice_period(raw: str) -> Dict:
    """Normalize notice period string to structured field."""
    if not raw:
        return {
            "raw": None,
            "normalized": NoticePeriod.UNKNOWN.value,
            "metadata": {}
        }
    
    raw_lower = raw.lower().strip()
    normalized = NOTICE_MAPPINGS.get(raw_lower, NoticePeriod.UNKNOWN)
    
    return {
        "raw": raw,
        "normalized": normalized.value,
        "metadata": {}
    }

def normalize_phone(raw: str, country: str = None) -> Dict:
    """
    Normalize phone number to E.164 format.
    Returns: { raw, normalized (E.164), formatted (display), countryCode }
    """
    if not raw:
        return {
            "raw": None,
            "normalized": None,
            "formatted": None,
            "metadata": {"countryCode": None}
        }
    
    # Clean - remove all non-digit except leading +
    has_plus = raw.strip().startswith('+')
    digits_only = re.sub(r'[^\d]', '', raw)
    
    # Detect country code
    country_code = None
    national_number = digits_only
    
    if has_plus or len(digits_only) > 10:
        # Has country code
        if digits_only.startswith('1') and len(digits_only) == 11:
            country_code = "+1"
            national_number = digits_only[1:]
        elif digits_only.startswith('44'):
            country_code = "+44"
            national_number = digits_only[2:]
        elif digits_only.startswith('61'):
            country_code = "+61"
            national_number = digits_only[2:]
        elif digits_only.startswith('91'):
            country_code = "+91"
            national_number = digits_only[2:]
        else:
            country_code = "+1"  # Default
            national_number = digits_only[-10:] if len(digits_only) > 10 else digits_only
    else:
        # No country code - infer from country
        if country:
            country_code = COUNTRY_PHONE_CODES.get(country.lower(), "+1")
        else:
            country_code = "+1"  # Default North America
    
    # E.164 format (normalized)
    e164 = f"{country_code}{national_number}"
    
    # Formatted for display
    if len(national_number) == 10:
        formatted = f"{country_code} ({national_number[:3]}) {national_number[3:6]}-{national_number[6:]}"
    else:
        formatted = e164
    
    return {
        "raw": raw,
        "normalized": e164,
        "formatted": formatted,
        "metadata": {"countryCode": country_code}
    }

def normalize_skill(skill: Any) -> Dict:
    """
    Normalize a single skill to structured field.
    Stores years as number, not bucket.
    """
    if isinstance(skill, str):
        return {
            "name": skill.strip(),
            "years": None,
            "level": None
        }
    elif isinstance(skill, dict):
        name = skill.get("name", "")
        years_raw = skill.get("years")
        
        # Convert bucket to number if needed
        if isinstance(years_raw, str):
            years = bucket_to_years(years_raw)
        else:
            years = years_raw
        
        level = skill.get("level")
        if level and isinstance(level, str):
            level = level.lower()
        
        return {
            "name": name.strip() if name else "",
            "years": years,
            "level": level
        }
    return None

def normalize_skills(skills: List) -> Dict:
    """
    Normalize skills list to structured array.
    Returns: { items: [{ name, years, level }] }
    """
    if not skills:
        return {"items": []}
    
    items = []
    for skill in skills:
        norm_skill = normalize_skill(skill)
        if norm_skill and norm_skill.get("name"):
            items.append(norm_skill)
    
    return {"items": items}

def normalize_links(profile: Dict) -> Dict:
    """Extract and normalize profile links."""
    return {
        "linkedin": profile.get("linkedin_url") or None,
        "github": profile.get("github_url") or None,
        "portfolio": profile.get("portfolio_url") or None,
        "website": profile.get("website_url") or None
    }

def normalize_preferences(profile: Dict) -> Dict:
    """Extract and normalize job preferences."""
    # Normalize work arrangement
    work_arrangement_raw = profile.get("preferred_work_arrangement", "")
    work_arrangement = WorkArrangement.UNKNOWN.value
    if work_arrangement_raw:
        work_arrangement = WORK_ARRANGEMENT_MAPPINGS.get(
            work_arrangement_raw.lower().strip(), 
            WorkArrangement.UNKNOWN
        ).value
    
    # Normalize job types
    job_types_raw = profile.get("job_type", [])
    job_types = []
    for jt in job_types_raw:
        if isinstance(jt, str):
            normalized_jt = JOB_TYPE_MAPPINGS.get(jt.lower().strip(), JobType.UNKNOWN)
            if normalized_jt != JobType.UNKNOWN:
                job_types.append(normalized_jt.value)
    
    # Normalize willing to relocate
    relocate_raw = profile.get("willing_to_relocate", "")
    relocate = WillingToRelocate.UNKNOWN.value
    if relocate_raw:
        relocate = RELOCATE_MAPPINGS.get(
            relocate_raw.lower().strip(),
            WillingToRelocate.UNKNOWN
        ).value
    
    # Normalize notice period
    notice_raw = profile.get("notice_period", "")
    notice = NoticePeriod.UNKNOWN.value
    if notice_raw:
        notice = NOTICE_MAPPINGS.get(
            notice_raw.lower().strip(),
            NoticePeriod.UNKNOWN
        ).value
    
    return {
        "desiredJobTitles": profile.get("job_titles", []),
        "preferredLocations": profile.get("preferred_locations", []),
        "workArrangement": work_arrangement,
        "jobTypes": job_types if job_types else [JobType.FULL_TIME.value],
        "willingToRelocate": relocate,
        "noticePeriod": notice,
        "availabilityDate": profile.get("availability_date")
    }

def normalize_compensation(profile: Dict) -> Dict:
    """Extract and normalize compensation expectations."""
    return {
        "salaryExpectations": {
            "min": profile.get("salary_min"),
            "max": profile.get("salary_max"),
            "currency": "USD"  # Default, could be inferred from country
        }
    }

def normalize_industries(profile: Dict) -> Dict:
    """Extract and normalize target industries."""
    return {
        "targetIndustries": profile.get("industries", []),
        "openToAny": profile.get("open_to_any_industry", False)
    }

def normalize_application_defaults(profile: Dict) -> Dict:
    """Extract and normalize application defaults."""
    return {
        "referralSource": profile.get("referral_source", "LinkedIn")
    }

def normalize_location(city: str, state: str, country: str) -> Dict:
    """Normalize location to structured field."""
    country_code = None
    if country:
        country_code = COUNTRY_CODES.get(country.lower().strip(), country.upper()[:2])
    
    return {
        "raw": {
            "city": city,
            "state": state,
            "country": country
        },
        "normalized": {
            "city": city.strip().title() if city else None,
            "state": state.strip() if state else None,
            "countryCode": country_code
        },
        "metadata": {
            "countryFull": country
        }
    }

def normalize_contact(profile: Dict) -> Dict:
    """Extract and normalize contact information."""
    phone_data = normalize_phone(
        profile.get("phone_number"),
        profile.get("address_country")
    )
    
    return {
        "email": profile.get("email"),
        "phone": phone_data,
        "location": normalize_location(
            profile.get("address_city"),
            profile.get("address_state"),
            profile.get("address_country")
        )
    }

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
        # Still refresh structured data in case schema evolved
        pass
    
    # Get country for context
    country = profile.get("address_country", "Canada")
    
    # Create structured fields
    structured = {
        "profile_version": 2,
        "migrated_at": datetime.now(timezone.utc).isoformat(),
        
        # Preserve all original fields for backwards compatibility
        **{k: v for k, v in profile.items() if k not in ["profile_version", "migrated_at", "structured"]},
        
        # Add structured versions
        "structured": {
            # Work authorization with country, status, sponsorship
            "workAuthorization": normalize_work_authorization(
                profile.get("work_authorization"),
                country
            ),
            
            # Seniority
            "seniorityLevel": normalize_seniority(profile.get("seniority_level")),
            
            # Education
            "education": normalize_education(profile.get("highest_education")),
            
            # Skills with numeric years
            "skills": normalize_skills(profile.get("skills", [])),
            
            # Contact info with E.164 phone
            "contact": normalize_contact(profile),
            
            # Links
            "links": normalize_links(profile),
            
            # Preferences
            "preferences": normalize_preferences(profile),
            
            # Compensation
            "compensation": normalize_compensation(profile),
            
            # Industries
            "industries": normalize_industries(profile),
            
            # Application defaults
            "applicationDefaults": normalize_application_defaults(profile),
        }
    }
    
    return structured

def get_skill_names(skills: Any) -> List[str]:
    """
    Extract just the skill names from skills data (works with v1 and v2 formats).
    Used for backwards-compatible matching logic.
    """
    if not skills:
        return []
    
    # Handle v2 structured format
    if isinstance(skills, dict) and "items" in skills:
        return [s.get("name", "").lower() for s in skills["items"] if s.get("name")]
    
    # Handle list format (v1 or v2 items directly)
    names = []
    if isinstance(skills, list):
        for skill in skills:
            if isinstance(skill, str):
                names.append(skill.lower())
            elif isinstance(skill, dict):
                name = skill.get("name", "")
                if name:
                    names.append(name.lower())
    
    return names

def get_normalized_value(profile: Dict, path: str, default: Any = None) -> Any:
    """
    Get a normalized value from the structured profile using dot notation.
    Falls back to raw value if normalized is 'unknown' or None.
    
    Example paths:
    - "workAuthorization.status"
    - "contact.phone.normalized"
    - "preferences.workArrangement"
    """
    structured = profile.get("structured", {})
    
    parts = path.split(".")
    current = structured
    
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return default
        
        if current is None:
            return default
    
    # Check if value is "unknown" and should fallback
    if current == "unknown" or current == EducationLevel.UNKNOWN.value:
        return default
    
    return current

def get_autofill_data(profile: Dict) -> Dict:
    """
    Extract all normalized data for auto-fill purposes.
    Returns a flat dict optimized for form filling.
    Uses ONLY normalized values, falls back to raw when no mapping exists.
    """
    if profile.get("profile_version") != 2:
        profile = migrate_profile_to_v2(profile)
    
    structured = profile.get("structured", {})
    
    # Get nested values safely
    work_auth = structured.get("workAuthorization", {})
    work_auth_norm = work_auth.get("normalized", {})
    
    contact = structured.get("contact", {})
    phone = contact.get("phone", {})
    location = contact.get("location", {})
    location_norm = location.get("normalized", {})
    
    links = structured.get("links", {})
    preferences = structured.get("preferences", {})
    compensation = structured.get("compensation", {})
    salary = compensation.get("salaryExpectations", {})
    industries = structured.get("industries", {})
    app_defaults = structured.get("applicationDefaults", {})
    skills_data = structured.get("skills", {})
    
    # Build autofill dict with normalized values
    autofill = {
        # Identity (from original profile)
        "firstName": profile.get("first_name", ""),
        "lastName": profile.get("last_name", ""),
        "fullName": profile.get("full_name", ""),
        
        # Contact - use normalized E.164 for forms
        "email": contact.get("email") or profile.get("email", ""),
        "phone": phone.get("normalized"),  # E.164 format
        "phoneFormatted": phone.get("formatted"),  # Display format
        "phoneCountryCode": phone.get("metadata", {}).get("countryCode"),
        
        # Location - use normalized
        "city": location_norm.get("city"),
        "state": location_norm.get("state"),
        "country": location_norm.get("countryCode"),
        "countryFull": location.get("metadata", {}).get("countryFull"),
        
        # Work Authorization - use normalized
        "workAuthorizationStatus": work_auth_norm.get("status"),
        "workAuthorizationCountry": work_auth_norm.get("country"),
        "requiresSponsorship": work_auth_norm.get("requiresSponsorship"),
        "workAuthorizationExpiry": work_auth_norm.get("expiryDate"),
        
        # Professional - use normalized enums
        "seniorityLevel": get_normalized_value(profile, "seniorityLevel.normalized"),
        "education": get_normalized_value(profile, "education.normalized"),
        "experienceYears": profile.get("experience_years", 0),
        
        # Preferences - use normalized
        "desiredJobTitles": preferences.get("desiredJobTitles", []),
        "preferredLocations": preferences.get("preferredLocations", []),
        "workArrangement": preferences.get("workArrangement"),
        "jobTypes": preferences.get("jobTypes", []),
        "willingToRelocate": preferences.get("willingToRelocate"),
        "noticePeriod": preferences.get("noticePeriod"),
        "availabilityDate": preferences.get("availabilityDate"),
        
        # Compensation
        "salaryMin": salary.get("min"),
        "salaryMax": salary.get("max"),
        "salaryCurrency": salary.get("currency", "USD"),
        
        # Links - direct values
        "linkedinUrl": links.get("linkedin"),
        "githubUrl": links.get("github"),
        "portfolioUrl": links.get("portfolio"),
        "websiteUrl": links.get("website"),
        
        # Industries
        "targetIndustries": industries.get("targetIndustries", []),
        "openToAnyIndustry": industries.get("openToAny", False),
        
        # Application defaults
        "referralSource": app_defaults.get("referralSource", "LinkedIn"),
        "currentCompany": profile.get("current_company", ""),
        
        # Skills - list of names for simple matching
        "skills": [s.get("name", "") for s in skills_data.get("items", []) if s.get("name")],
        
        # Skills with years - full structured data
        "skillsWithYears": [
            {
                "name": s.get("name"),
                "years": s.get("years"),
                "yearsBucket": years_to_bucket(s.get("years")),
                "level": s.get("level")
            }
            for s in skills_data.get("items", [])
            if s.get("name")
        ],
    }
    
    return autofill

def handle_v1_profile_update(update_data: Dict, existing_profile: Dict = None) -> Dict:
    """
    Handle a v1 format profile update payload.
    Converts to v2 format before saving.
    """
    # If update_data has v1 fields, convert them
    converted = update_data.copy()
    
    # Handle skills - convert bucket years to numeric
    if "skills" in converted:
        skills = converted["skills"]
        if isinstance(skills, list):
            normalized_skills = []
            for skill in skills:
                if isinstance(skill, str):
                    normalized_skills.append({"name": skill, "years": None, "level": None})
                elif isinstance(skill, dict):
                    years = skill.get("years")
                    if isinstance(years, str):
                        years = bucket_to_years(years)
                    normalized_skills.append({
                        "name": skill.get("name", ""),
                        "years": years,
                        "level": skill.get("level")
                    })
            converted["skills"] = normalized_skills
    
    # Set version
    converted["profile_version"] = 2
    converted["migrated_at"] = datetime.now(timezone.utc).isoformat()
    
    return converted
