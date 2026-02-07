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

# SmartRecruiters - Canadian companies with active job boards
# Format: company slug as it appears in jobs.smartrecruiters.com/{slug} or careers.smartrecruiters.com/{slug}
SMARTRECRUITERS_COMPANIES = [
    # Major Canadian Tech Companies
    "Shopify5",  # Shopify
    "Wealthsimple",
    "Clio",
    "Hootsuite", 
    "ApplyBoard",
    "Vidyard",
    "Clearco",
    "Benevity",
    "Unbounce",
    "ArticleGroup",  # Article
    "Lightspeed",
    "Coveo",
    "Nuvei",
    "TouchBistro",
    "Thinkific",
    "Ada",  # Ada Support
    "Trulioo",
    "Dialogue1",
    "Clearbanc",
    "Tulip",
    "Borrowell",
    "Kira",
    "FreshBooks",
    "Koho",
    "Wave",  # Wave Financial
    "Vendasta",
    "Bench1",
    "SkipTheDishes",
    "Ritual",
    "League",
    # Additional verified Canadian companies
    "ampleinsightinc",  # Ample Insight Inc. (verified)
    "CSGROUP/cscanada",  # CS GROUP Canada (verified)
    "Indigo",  # Indigo Books (verified)
    # Enterprise/Large Canadian companies
    "RBC",
    "TD",
    "BMO",
    "ScotiabankGroup",
    "CIBC",
    "SunLife",
    "ManulifeFinancialCorporation",
    "Telus",
    "Bell",
    "Rogers",
    "LoblawCompaniesLimited",
    # Canadian Crown Corporations & Government
    "CanadaPost",
    "VIARail",
]

# Pinpoint - Canadian companies with active job boards
# Format: subdomain as it appears in {subdomain}.pinpointhq.com
PINPOINT_COMPANIES = [
    # Note: Pinpoint is less common in Canada, these are known users
    "workwithus",  # Pinpoint's own board (for testing)
    # Add more Canadian companies as they're discovered
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
    Fetch jobs from a SmartRecruiters company career page.
    
    Note: SmartRecruiters uses heavy client-side rendering with React.
    This basic scraper tries to extract job data from the initial page load,
    but may miss jobs that are loaded dynamically. For full coverage,
    Playwright-based scraping would be needed.
    """
    jobs = []
    
    # SmartRecruiters has two URL patterns
    urls_to_try = [
        f"https://careers.smartrecruiters.com/{company_slug}",
        f"https://jobs.smartrecruiters.com/{company_slug}"
    ]
    
    for base_url in urls_to_try:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    base_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                    },
                    follow_redirects=True
                )
                
                if response.status_code != 200:
                    continue
                
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract company name from page
                company_name = company_slug.replace("-", " ").replace("_", " ")
                title_tag = soup.find('title')
                if title_tag and title_tag.string:
                    title_match = re.search(r'Careers at (.+?)(?:\s*\||$)', title_tag.string, re.IGNORECASE)
                    if title_match:
                        company_name = title_match.group(1).strip()
                
                # Look for job listings in the HTML
                # SmartRecruiters uses various patterns
                
                # Pattern 1: Look for job links
                job_links = soup.find_all('a', href=re.compile(r'/\d+[-\w]*$'))
                
                for link in job_links:
                    href = link.get('href', '')
                    if not href or '/privacy' in href or '/cookies' in href:
                        continue
                    
                    # Extract job title from link text or parent
                    title_text = link.get_text(strip=True)
                    if not title_text or len(title_text) < 5:
                        continue
                    
                    # Try to find location nearby
                    parent = link.find_parent(['li', 'div', 'article'])
                    location = ""
                    if parent:
                        location_elem = parent.find(class_=re.compile(r'location', re.I))
                        if location_elem:
                            location = location_elem.get_text(strip=True)
                    
                    # Check if Canadian job
                    if is_canadian_job(location, ""):
                        job_id = href.split('/')[-1]
                        apply_link = href if href.startswith('http') else f"{base_url}{href}"
                        
                        jobs.append(normalize_job({
                            "job_id": f"sr_{company_slug}_{job_id}",
                            "title": title_text,
                            "company": company_name,
                            "location": location,
                            "description": "",
                            "apply_link": apply_link,
                        }, "smartrecruiters"))
                
                # Pattern 2: Look for JSON data in script tags
                import json
                script_tags = soup.find_all('script', type='application/json')
                for script in script_tags:
                    try:
                        data = json.loads(script.string or '{}')
                        if isinstance(data, dict):
                            # Check various possible structures
                            job_list = data.get('jobs', []) or data.get('postings', []) or data.get('content', [])
                            if not job_list and 'data' in data:
                                job_list = data['data'] if isinstance(data['data'], list) else []
                            
                            for job in job_list:
                                if not isinstance(job, dict):
                                    continue
                                    
                                job_location = job.get('location', {})
                                if isinstance(job_location, dict):
                                    location_str = f"{job_location.get('city', '')}, {job_location.get('region', '')}".strip(", ")
                                else:
                                    location_str = str(job_location) if job_location else ""
                                
                                if is_canadian_job(location_str, job.get('description', '')):
                                    jobs.append(normalize_job({
                                        "job_id": f"sr_{company_slug}_{job.get('id', job.get('uuid', ''))}",
                                        "title": job.get('name') or job.get('title'),
                                        "company": company_name,
                                        "location": location_str,
                                        "description": job.get('description', ''),
                                        "apply_link": job.get('applyUrl') or f"{base_url}/{job.get('id')}",
                                        "employment_type": job.get('typeOfEmployment'),
                                        "department": job.get('department', {}).get('label') if isinstance(job.get('department'), dict) else job.get('department'),
                                    }, "smartrecruiters"))
                    except (json.JSONDecodeError, TypeError):
                        continue
                
                if jobs:
                    break  # Found jobs, no need to try other URL
                
        except Exception as e:
            logger.debug(f"SmartRecruiters {company_slug} ({base_url}): {str(e)}")
            continue
    
    logger.info(f"SmartRecruiters {company_slug}: Found {len(jobs)} Canadian jobs")
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
