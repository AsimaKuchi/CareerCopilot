"""
ATS Job Board Scrapers
Fetches jobs from various ATS platforms (SmartRecruiters, Pinpoint, etc.)
All scrapers return normalized job data compatible with the existing schema.
"""

import httpx
import asyncio
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime, timezone
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ========================
# CANADIAN COMPANY LISTS
# ========================

# SmartRecruiters - Companies with verified active job boards
# Format: company slug as it appears in api.smartrecruiters.com/v1/companies/{slug}/postings
SMARTRECRUITERS_COMPANIES = [
    # Companies with verified public API access and Canadian presence
    "Visa",           # Large employer, has Canadian offices
    "Dexterra",       # Canadian company
    "Ericsson",       # Has Canadian offices
    "IBM",            # Has Canadian offices
    "Accenture",      # Has Canadian offices  
    "Salesforce",     # Has Canadian offices
    "SAP",            # Has Canadian offices
    "Oracle",         # Has Canadian offices
    "Microsoft",      # Has Canadian offices
    "Amazon",         # Has Canadian offices
    "Google",         # Has Canadian offices
    "Meta",           # Has Canadian offices
    "Stripe",         # Has Canadian presence
    "Datadog",        # Has Canadian presence
    "Twilio",         # Has Canadian presence
    "Atlassian",      # Has Canadian presence
    "Snowflake",      # Has Canadian presence
    "Databricks",     # Has Canadian presence
    "Confluent",      # Has Canadian presence
]

# Pinpoint - Companies with verified Canadian presence
# Format: subdomain as it appears in {subdomain}.pinpointhq.com
# Note: Pinpoint is less common in Canada - add companies as they're discovered
PINPOINT_COMPANIES = [
    # Most Pinpoint users are UK-based
    # Add Canadian companies here as they're found
    # "example-canadian-company",
]

# Canadian provinces and cities for location filtering
CANADIAN_LOCATIONS = [
    "canada", "toronto", "vancouver", "montreal", "ottawa", "calgary", 
    "edmonton", "winnipeg", "quebec", "hamilton", "kitchener", "waterloo",
    "london", "victoria", "halifax", "saskatoon", "regina", "st. john",
    "ontario", "british columbia", "bc", "quebec", "alberta", "manitoba",
    "saskatchewan", "nova scotia", "new brunswick", "newfoundland",
    "prince edward island", "yukon", "nunavut", "northwest territories",
    "gta", "greater toronto", "remote - canada", "canada remote"
]


def is_canadian_job(location: str, description: str = "") -> bool:
    """Check if a job is located in Canada based on location and description."""
    if not location:
        return False
    
    location_lower = location.lower()
    desc_lower = (description or "").lower()
    
    # First check for non-Canadian country indicators - exclude these
    non_canadian_indicators = [
        "united kingdom", "uk", ", gb", "england", "scotland", "wales",
        "united states", "usa", ", us", "america",
        "germany", "france", "spain", "italy", "netherlands", "australia",
        "india", "singapore", "japan", "china", "brazil", "mexico"
    ]
    
    for indicator in non_canadian_indicators:
        if indicator in location_lower:
            # Exception: "Remote - US/Canada" or similar should still pass
            if "canada" in location_lower:
                break
            return False
    
    # Check for Canadian location keywords
    for loc in CANADIAN_LOCATIONS:
        if loc in location_lower:
            return True
    
    # Check description for Canada mentions (for remote jobs)
    if "remote" in location_lower:
        # Check if description mentions Canada eligibility
        canada_patterns = [
            "canada", "canadian", "ontario", "british columbia", "quebec",
            "alberta", "toronto", "vancouver", "montreal"
        ]
        for pattern in canada_patterns:
            if pattern in desc_lower:
                return True
    
    return False


def normalize_job(job_data: Dict, ats_type: str) -> Dict:
    """
    Normalize job data from any ATS into the standard schema.
    """
    return {
        "job_id": job_data.get("job_id"),
        "title": job_data.get("title"),
        "company": job_data.get("company"),
        "location": job_data.get("location"),
        "description": job_data.get("description", "")[:500] + "..." if job_data.get("description") else "",
        "full_description": job_data.get("full_description") or job_data.get("description", ""),
        "apply_link": job_data.get("apply_link"),
        "posted_at": job_data.get("posted_at"),
        "source": ats_type,
        "ats_type": ats_type,
        "source_platform": ats_type,
        "employment_type": job_data.get("employment_type"),
        "workplace_type": job_data.get("workplace_type"),  # remote, hybrid, onsite
        "department": job_data.get("department"),
        "salary_min": job_data.get("salary_min"),
        "salary_max": job_data.get("salary_max"),
        "salary_currency": job_data.get("salary_currency"),
    }


# ========================
# SMARTRECRUITERS SCRAPER
# ========================

async def fetch_smartrecruiters_jobs(company_slug: str) -> List[Dict]:
    """
    Fetch jobs from SmartRecruiters using their public API.
    API endpoint: api.smartrecruiters.com/v1/companies/{company}/postings
    """
    jobs = []
    api_url = f"https://api.smartrecruiters.com/v1/companies/{company_slug}/postings"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Fetch first page
            params = {"limit": 100, "offset": 0}
            response = await client.get(
                api_url,
                params=params,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code != 200:
                logger.debug(f"SmartRecruiters {company_slug}: HTTP {response.status_code}")
                return jobs
            
            data = response.json()
            postings = data.get("content", [])
            total_found = data.get("totalFound", 0)
            
            logger.info(f"SmartRecruiters {company_slug}: {total_found} total jobs, processing {len(postings)}")
            
            for posting in postings:
                # Extract location info
                location_data = posting.get("location", {})
                city = location_data.get("city", "")
                region = location_data.get("region", "")
                country = location_data.get("country", "")
                remote = location_data.get("remote", False)
                
                location_str = ", ".join(filter(None, [city, region, country]))
                if remote:
                    location_str = f"Remote - {location_str}" if location_str else "Remote"
                
                # Get description
                job_ad = posting.get("jobAd", {})
                description = ""
                sections = job_ad.get("sections", {})
                if sections:
                    # Combine job description sections
                    desc_parts = []
                    for section_name in ["jobDescription", "qualifications", "additionalInformation"]:
                        section = sections.get(section_name, {})
                        if section.get("text"):
                            desc_parts.append(section["text"])
                    description = "\n".join(desc_parts)
                
                # Clean HTML from description
                if description:
                    soup = BeautifulSoup(description, 'html.parser')
                    description = soup.get_text(separator=" ", strip=True)
                
                # Check if it's a Canadian job
                if is_canadian_job(location_str, description):
                    # Get employment type
                    type_of_employment = posting.get("typeOfEmployment", {})
                    employment_type = type_of_employment.get("label") if isinstance(type_of_employment, dict) else str(type_of_employment)
                    
                    # Get department
                    department = posting.get("department", {})
                    dept_name = department.get("label") if isinstance(department, dict) else str(department) if department else None
                    
                    # Build apply link
                    posting_id = posting.get("id") or posting.get("uuid")
                    ref_number = posting.get("refNumber", "")
                    apply_link = f"https://jobs.smartrecruiters.com/{company_slug}/{posting_id}"
                    if ref_number:
                        apply_link = f"https://jobs.smartrecruiters.com/{company_slug}/{posting_id}-{ref_number}"
                    
                    jobs.append(normalize_job({
                        "job_id": f"sr_{company_slug}_{posting_id}",
                        "title": posting.get("name"),
                        "company": posting.get("company", {}).get("name", company_slug),
                        "location": location_str,
                        "description": description[:500] + "..." if len(description) > 500 else description,
                        "full_description": description,
                        "apply_link": apply_link,
                        "posted_at": posting.get("releasedDate"),
                        "employment_type": employment_type,
                        "department": dept_name,
                    }, "smartrecruiters"))
            
            logger.info(f"SmartRecruiters {company_slug}: Found {len(jobs)} Canadian jobs")
            
    except Exception as e:
        logger.error(f"SmartRecruiters {company_slug} error: {str(e)}")
    
    return jobs


async def fetch_all_smartrecruiters_jobs() -> List[Dict]:
    """Fetch jobs from all SmartRecruiters companies in parallel."""
    all_jobs = []
    
    # Fetch in batches of 10 to avoid overwhelming the server
    batch_size = 10
    for i in range(0, len(SMARTRECRUITERS_COMPANIES), batch_size):
        batch = SMARTRECRUITERS_COMPANIES[i:i + batch_size]
        tasks = [fetch_smartrecruiters_jobs(company) for company in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_jobs.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"SmartRecruiters batch error: {result}")
        
        # Small delay between batches
        if i + batch_size < len(SMARTRECRUITERS_COMPANIES):
            await asyncio.sleep(1)
    
    logger.info(f"SmartRecruiters total: {len(all_jobs)} Canadian jobs from {len(SMARTRECRUITERS_COMPANIES)} companies")
    return all_jobs


# ========================
# PINPOINT SCRAPER
# ========================

async def fetch_pinpoint_jobs(company_subdomain: str) -> List[Dict]:
    """
    Fetch jobs from a Pinpoint company career page.
    Pinpoint has a public JSON endpoint at {subdomain}.pinpointhq.com/postings.json
    """
    jobs = []
    url = f"https://{company_subdomain}.pinpointhq.com/postings.json"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code != 200:
                logger.warning(f"Pinpoint {company_subdomain}: HTTP {response.status_code}")
                return jobs
            
            data = response.json()
            postings = data.get("data", [])
            
            for posting in postings:
                # Extract location info
                location_data = posting.get("location", {})
                location_str = f"{location_data.get('city', '')}, {location_data.get('name', '')}".strip(", ")
                
                # Get description (clean HTML)
                description = posting.get("description", "")
                if description:
                    soup = BeautifulSoup(description, 'html.parser')
                    description = soup.get_text(separator=" ", strip=True)
                
                # Check if it's a Canadian job
                if is_canadian_job(location_str, description):
                    job_data = posting.get("job", {})
                    department = job_data.get("department", {})
                    
                    jobs.append(normalize_job({
                        "job_id": f"pinpoint_{company_subdomain}_{posting.get('id')}",
                        "title": posting.get("title"),
                        "company": company_subdomain.replace("-", " ").title(),
                        "location": location_str,
                        "description": description,
                        "full_description": description,
                        "apply_link": posting.get("url"),
                        "employment_type": posting.get("employment_type_text"),
                        "workplace_type": posting.get("workplace_type_text"),
                        "department": department.get("name") if isinstance(department, dict) else None,
                        "salary_min": posting.get("compensation_minimum"),
                        "salary_max": posting.get("compensation_maximum"),
                        "salary_currency": posting.get("compensation_currency"),
                    }, "pinpoint"))
            
            logger.info(f"Pinpoint {company_subdomain}: Found {len(jobs)} Canadian jobs")
            
    except Exception as e:
        logger.error(f"Pinpoint {company_subdomain} error: {str(e)}")
    
    return jobs


async def fetch_all_pinpoint_jobs() -> List[Dict]:
    """Fetch jobs from all Pinpoint companies in parallel."""
    all_jobs = []
    
    tasks = [fetch_pinpoint_jobs(company) for company in PINPOINT_COMPANIES]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if isinstance(result, list):
            all_jobs.extend(result)
        elif isinstance(result, Exception):
            logger.error(f"Pinpoint error: {result}")
    
    logger.info(f"Pinpoint total: {len(all_jobs)} Canadian jobs from {len(PINPOINT_COMPANIES)} companies")
    return all_jobs


# ========================
# COMBINED FETCHER
# ========================

async def fetch_all_new_ats_jobs() -> Dict[str, List[Dict]]:
    """
    Fetch jobs from all new ATS platforms.
    Returns a dict with jobs grouped by ATS type.
    """
    results = {
        "smartrecruiters": [],
        "pinpoint": [],
    }
    
    # Fetch from all platforms in parallel
    sr_task = fetch_all_smartrecruiters_jobs()
    pp_task = fetch_all_pinpoint_jobs()
    
    sr_jobs, pp_jobs = await asyncio.gather(sr_task, pp_task, return_exceptions=True)
    
    if isinstance(sr_jobs, list):
        results["smartrecruiters"] = sr_jobs
    else:
        logger.error(f"SmartRecruiters fetch failed: {sr_jobs}")
    
    if isinstance(pp_jobs, list):
        results["pinpoint"] = pp_jobs
    else:
        logger.error(f"Pinpoint fetch failed: {pp_jobs}")
    
    total = sum(len(jobs) for jobs in results.values())
    logger.info(f"New ATS total: {total} jobs (SmartRecruiters: {len(results['smartrecruiters'])}, Pinpoint: {len(results['pinpoint'])})")
    
    return results


async def fetch_all_new_ats_jobs_flat() -> List[Dict]:
    """
    Fetch jobs from all new ATS platforms and return as a flat list.
    """
    results = await fetch_all_new_ats_jobs()
    all_jobs = []
    
    for ats_type, jobs in results.items():
        all_jobs.extend(jobs)
    
    return all_jobs
