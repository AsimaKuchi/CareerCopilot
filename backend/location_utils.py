"""
Location parsing and filtering utilities for job search.
Handles remote job scoping, country detection, and location normalization.
"""

import re
from typing import Dict, Optional, Tuple

# Canadian provinces and territories
CANADIAN_PROVINCES = {
    "ontario": "ON",
    "quebec": "QC", 
    "british columbia": "BC",
    "alberta": "AB",
    "manitoba": "MB",
    "saskatchewan": "SK",
    "nova scotia": "NS",
    "new brunswick": "NB",
    "newfoundland": "NL",
    "newfoundland and labrador": "NL",
    "prince edward island": "PE",
    "yukon": "YT",
    "nunavut": "NU",
    "northwest territories": "NT",
    # Abbreviations
    "on": "ON", "qc": "QC", "bc": "BC", "ab": "AB", "mb": "MB",
    "sk": "SK", "ns": "NS", "nb": "NB", "nl": "NL", "pe": "PE",
    "yt": "YT", "nu": "NU", "nt": "NT",
}

# Major Canadian cities mapped to provinces
CANADIAN_CITIES = {
    "toronto": "ON", "ottawa": "ON", "mississauga": "ON", "brampton": "ON",
    "hamilton": "ON", "london": "ON", "markham": "ON", "vaughan": "ON",
    "kitchener": "ON", "windsor": "ON", "waterloo": "ON", "guelph": "ON",
    "montreal": "QC", "quebec city": "QC", "laval": "QC", "gatineau": "QC",
    "vancouver": "BC", "surrey": "BC", "burnaby": "BC", "richmond": "BC", "victoria": "BC",
    "calgary": "AB", "edmonton": "AB", "red deer": "AB",
    "winnipeg": "MB",
    "saskatoon": "SK", "regina": "SK",
    "halifax": "NS",
    "saint john": "NB", "moncton": "NB", "fredericton": "NB",
    "st. john's": "NL",
    "charlottetown": "PE",
}

# US states (to detect and exclude)
US_STATES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york", "north carolina",
    "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania",
    "rhode island", "south carolina", "south dakota", "tennessee", "texas",
    "utah", "vermont", "virginia", "washington", "west virginia",
    "wisconsin", "wyoming",
    # Abbreviations
    "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga", "hi", "id",
    "il", "in", "ia", "ks", "ky", "la", "me", "md", "ma", "mi", "mn", "ms",
    "mo", "mt", "ne", "nv", "nh", "nj", "nm", "ny", "nc", "nd", "oh", "ok",
    "or", "pa", "ri", "sc", "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv",
    "wi", "wy",
}

# Major US cities (to detect and exclude for Canadian searches)
US_CITIES = {
    "new york", "los angeles", "chicago", "houston", "phoenix", "philadelphia",
    "san antonio", "san diego", "dallas", "san jose", "austin", "jacksonville",
    "fort worth", "columbus", "charlotte", "san francisco", "indianapolis",
    "seattle", "denver", "boston", "nashville", "detroit", "portland",
    "las vegas", "memphis", "louisville", "baltimore", "milwaukee",
    "albuquerque", "tucson", "fresno", "sacramento", "kansas city",
    "atlanta", "miami", "raleigh", "omaha", "oakland", "minneapolis",
}

# Global/Worldwide remote indicators
GLOBAL_REMOTE_INDICATORS = [
    "remote - global", "global remote", "worldwide", "work from anywhere",
    "remote - worldwide", "remote worldwide", "fully remote - global",
    "remote (global)", "remote (worldwide)", "anywhere in the world",
    "location flexible", "work from home - global",
]

# North America remote indicators
NORTH_AMERICA_REMOTE_INDICATORS = [
    "remote - north america", "north america remote", "remote (north america)",
    "us/canada remote", "canada/us remote", "remote - us & canada",
    "remote - usa/canada", "remote north america",
]

# Canada-specific remote indicators
CANADA_REMOTE_INDICATORS = [
    "remote - canada", "canada remote", "remote (canada)", "canadian remote",
    "remote - canadian", "work from home - canada", "remote canada only",
    "remote (canadian)", "canada only - remote",
]

# US-only remote indicators (to exclude for Canadian searches)
US_ONLY_REMOTE_INDICATORS = [
    "remote - us", "us remote", "remote (us)", "usa remote", "remote - usa",
    "remote (usa)", "us only", "usa only", "united states only",
    "remote - united states", "us-based remote", "remote us only",
]


def parse_location(location_str: str, job_country: str = "", job_state: str = "", job_city: str = "") -> Dict:
    """
    Parse a location string into structured components.
    
    Returns:
    {
        "city": str or None,
        "province": str or None (Canadian province code),
        "state": str or None (US state),
        "country": str or None (country code: CA, US, etc.),
        "remote": bool,
        "remote_scope": "city" | "province" | "country" | "continent" | "global" | None,
        "remote_label": str (human-readable label like "Remote (Canada)"),
        "is_hybrid": bool,
        "raw_location": str,
    }
    """
    if not location_str:
        location_str = ""
    
    location_lower = location_str.lower().strip()
    job_country_lower = (job_country or "").lower().strip()
    job_state_lower = (job_state or "").lower().strip()
    job_city_lower = (job_city or "").lower().strip()
    
    # Combine all location info
    full_location = f"{location_lower} {job_city_lower} {job_state_lower} {job_country_lower}".strip()
    
    result = {
        "city": None,
        "province": None,
        "state": None,
        "country": None,
        "remote": False,
        "remote_scope": None,
        "remote_label": None,
        "is_hybrid": False,
        "raw_location": location_str,
    }
    
    # Check for hybrid
    if "hybrid" in location_lower:
        result["is_hybrid"] = True
    
    # Check for remote
    is_remote = any(term in location_lower for term in ["remote", "work from home", "wfh", "telecommute"])
    result["remote"] = is_remote
    
    # Determine remote scope
    if is_remote:
        # Check for global/worldwide remote (least restrictive)
        if any(indicator in location_lower for indicator in GLOBAL_REMOTE_INDICATORS):
            result["remote_scope"] = "global"
            result["remote_label"] = "Remote (Global)"
        # Check for North America remote
        elif any(indicator in location_lower for indicator in NORTH_AMERICA_REMOTE_INDICATORS):
            result["remote_scope"] = "continent"
            result["remote_label"] = "Remote (North America)"
        # Check for Canada-specific remote
        elif any(indicator in location_lower for indicator in CANADA_REMOTE_INDICATORS):
            result["remote_scope"] = "country"
            result["remote_label"] = "Remote (Canada)"
            result["country"] = "CA"
        # Check for US-only remote
        elif any(indicator in location_lower for indicator in US_ONLY_REMOTE_INDICATORS):
            result["remote_scope"] = "country"
            result["remote_label"] = "Remote (US Only)"
            result["country"] = "US"
        # Infer scope from other location clues
        else:
            # Default: try to determine scope from location hints
            result["remote_scope"] = "unknown"
            result["remote_label"] = "Remote"
    
    # Detect country
    if "canada" in full_location or job_country_lower in ["ca", "canada"]:
        result["country"] = "CA"
        if is_remote and result["remote_scope"] == "unknown":
            result["remote_scope"] = "country"
            result["remote_label"] = "Remote (Canada)"
    elif "united states" in full_location or "usa" in full_location or job_country_lower in ["us", "usa", "united states"]:
        result["country"] = "US"
        if is_remote and result["remote_scope"] == "unknown":
            result["remote_scope"] = "country"
            result["remote_label"] = "Remote (US)"
    elif "united kingdom" in full_location or "uk" in full_location or job_country_lower in ["uk", "gb", "united kingdom"]:
        result["country"] = "GB"
        if is_remote and result["remote_scope"] == "unknown":
            result["remote_scope"] = "country"
            result["remote_label"] = "Remote (UK)"
    
    # Detect Canadian city/province
    for city, prov in CANADIAN_CITIES.items():
        if city in full_location:
            result["city"] = city.title()
            result["province"] = prov
            result["country"] = "CA"
            if is_remote and result["remote_scope"] == "unknown":
                result["remote_scope"] = "city"
                result["remote_label"] = f"Remote ({city.title()}, {prov})"
            break
    
    # Detect Canadian province
    if not result["province"]:
        for prov_name, prov_code in CANADIAN_PROVINCES.items():
            if prov_name in full_location:
                result["province"] = prov_code
                result["country"] = "CA"
                if is_remote and result["remote_scope"] == "unknown":
                    result["remote_scope"] = "province"
                    result["remote_label"] = f"Remote ({prov_code}, Canada)"
                break
    
    # Detect US state (to potentially exclude)
    for state in US_STATES:
        if state in full_location:
            result["state"] = state.upper() if len(state) == 2 else state.title()
            if not result["country"]:
                result["country"] = "US"
            break
    
    # Detect US city
    for city in US_CITIES:
        if city in full_location:
            result["city"] = city.title()
            result["country"] = "US"
            break
    
    return result


def is_job_valid_for_canadian_search(parsed_location: Dict, user_city: str = None, user_province: str = None) -> Tuple[bool, str]:
    """
    Determine if a job should be shown to a Canadian user searching for jobs.
    
    Args:
        parsed_location: Output from parse_location()
        user_city: User's preferred city (e.g., "Toronto")
        user_province: User's preferred province code (e.g., "ON")
    
    Returns:
        Tuple of (is_valid, reason)
    """
    user_city_lower = (user_city or "").lower()
    user_province_upper = (user_province or "").upper()
    
    # If job explicitly has country and it's not Canada, reject
    if parsed_location["country"] == "US":
        # Exception: North America remote jobs are OK
        if parsed_location["remote"] and parsed_location["remote_scope"] == "continent":
            return True, "Remote job available in North America"
        return False, "Job is in the US, not Canada"
    
    # If job is remote
    if parsed_location["remote"]:
        remote_scope = parsed_location["remote_scope"]
        
        # Global remote - exclude unless explicitly allowed
        if remote_scope == "global":
            return False, "Global remote job - may not be eligible for Canadian residents"
        
        # US-only remote - reject
        if remote_scope == "country" and parsed_location["country"] == "US":
            return False, "Remote job is US-only"
        
        # Canada remote - accept
        if remote_scope == "country" and parsed_location["country"] == "CA":
            return True, "Remote job available in Canada"
        
        # North America remote - accept
        if remote_scope == "continent":
            return True, "Remote job available in North America (includes Canada)"
        
        # Province-scoped remote - check if matches user's province
        if remote_scope == "province":
            if user_province_upper and parsed_location["province"] == user_province_upper:
                return True, f"Remote job available in {user_province_upper}"
            elif not user_province_upper:
                return True, "Remote job with province scope"
            else:
                return False, f"Remote job only available in {parsed_location['province']}"
        
        # City-scoped remote - check if matches user's city
        if remote_scope == "city":
            job_city = (parsed_location["city"] or "").lower()
            if user_city_lower and job_city == user_city_lower:
                return True, f"Remote job based in {parsed_location['city']}"
            elif not user_city_lower:
                return True, "Remote job with city scope"
            # Allow if same province
            elif user_province_upper and parsed_location["province"] == user_province_upper:
                return True, f"Remote job in {parsed_location['city']}, {parsed_location['province']}"
        
        # Unknown scope remote - check for Canada indicators
        if remote_scope == "unknown":
            if parsed_location["country"] == "CA":
                return True, "Remote job appears to be in Canada"
            # Check if any Canadian indicators in raw location
            raw_lower = parsed_location["raw_location"].lower()
            if any(city in raw_lower for city in CANADIAN_CITIES.keys()):
                return True, "Remote job mentions Canadian city"
            if any(prov in raw_lower for prov, code in CANADIAN_PROVINCES.items() if len(prov) > 2):
                return True, "Remote job mentions Canadian province"
            # Be conservative - unknown remote jobs might not be available in Canada
            return False, "Remote job location unclear - may not be available in Canada"
    
    # Non-remote job (office or hybrid) - must be in Canada
    if parsed_location["country"] == "CA":
        # Check city match if user specified a city
        if user_city_lower:
            job_city = (parsed_location["city"] or "").lower()
            if job_city and job_city != user_city_lower:
                # Check if same province at least
                if user_province_upper and parsed_location["province"] == user_province_upper:
                    return True, f"Office job in {parsed_location['city']}, {parsed_location['province']}"
                return False, f"Office job in {parsed_location['city']}, not {user_city.title()}"
        return True, "Office/hybrid job in Canada"
    
    # No country detected - check for Canadian indicators
    if parsed_location["province"]:
        return True, f"Job appears to be in {parsed_location['province']}, Canada"
    
    if parsed_location["city"]:
        city_lower = parsed_location["city"].lower()
        if city_lower in CANADIAN_CITIES:
            return True, f"Job appears to be in {parsed_location['city']}, Canada"
    
    # Check raw location for any Canadian mentions
    raw_lower = parsed_location["raw_location"].lower()
    if "canada" in raw_lower:
        return True, "Job mentions Canada"
    for city in CANADIAN_CITIES.keys():
        if city in raw_lower:
            return True, f"Job mentions {city.title()}"
    
    # Unknown location - reject to be safe
    return False, "Job location unclear - cannot confirm it's in Canada"


def get_remote_label_for_display(parsed_location: Dict) -> Optional[str]:
    """
    Get a display label for remote jobs.
    Returns None for non-remote jobs.
    """
    if not parsed_location["remote"]:
        return None
    
    if parsed_location["remote_label"]:
        return parsed_location["remote_label"]
    
    # Fallback based on scope
    scope = parsed_location["remote_scope"]
    if scope == "global":
        return "Remote (Global)"
    elif scope == "continent":
        return "Remote (North America)"
    elif scope == "country":
        country = parsed_location["country"]
        if country == "CA":
            return "Remote (Canada)"
        elif country == "US":
            return "Remote (US)"
        elif country == "GB":
            return "Remote (UK)"
        return f"Remote ({country})"
    elif scope == "province":
        return f"Remote ({parsed_location['province']}, Canada)"
    elif scope == "city":
        return f"Remote ({parsed_location['city']})"
    
    return "Remote"
