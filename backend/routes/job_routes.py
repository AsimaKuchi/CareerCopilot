"""
routes/job_routes.py - Job search, ingestion helpers, Greenhouse/Lever/JSearch integrations.

Endpoints (under /api):
  POST /jobs/greenhouse/search        -- Search across Greenhouse companies
  GET  /jobs/saved                    -- List user's saved jobs
  GET  /jobs/greenhouse/companies     -- List supported companies
  POST /jobs/greenhouse/add-company   -- Submit a company suggestion
  POST /jobs/search                   -- Multi-source streaming job search
                                          (Greenhouse + Lever + JSearch + ATS)

Helpers (also re-exported for the scheduler):
  fetch_greenhouse_company_jobs, fetch_greenhouse_job_details
  fetch_lever_company_jobs, fetch_ashby_company_jobs
  fetch_amazon_jobs, fetch_company_jobs_via_jsearch
  cleanup_expired_jobs, fetch_all_jobs_parallel
  get_cached_jobs, save_jobs_to_cache
  search_greenhouse_jobs, enrich_greenhouse_job
  evaluate_job_match, calculate_match_score

Refactored from monolithic server.py (Feb 2026).
"""
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
import asyncio
import json
import re
import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
import httpx
from bs4 import BeautifulSoup

from core import (
    db,
    logger,
    RAPIDAPI_KEY,
    EMERGENT_LLM_KEY,
    GREENHOUSE_COMPANIES,
    LEVER_COMPANIES,
    ASHBY_COMPANIES,
    CUSTOM_CAREER_COMPANIES,
    JOB_CACHE_TTL_MINUTES,
    PARALLEL_BATCH_SIZE,
    is_english_job,
    normalize_posted_date,
    expand_query,
    parse_salary_from_description,
    format_salary_range,
    get_current_user,
)
from models import JobSearchQuery
from profile_schema import get_skill_names, normalize_skills
from ats_scrapers import (
    fetch_all_new_ats_jobs_flat,
    fetch_all_smartrecruiters_jobs,
    fetch_all_pinpoint_jobs,
    SMARTRECRUITERS_COMPANIES,
    PINPOINT_COMPANIES,
)
from location_utils import (
    parse_location,
    is_job_valid_for_canadian_search,
    get_remote_label_for_display,
    CANADIAN_CITIES,
    CANADIAN_PROVINCES,
)

router = APIRouter()


async def fetch_greenhouse_company_jobs(company: str) -> List[Dict]:
    """Fetch all jobs from a company's Greenhouse board using their API."""
    jobs = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            api_url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"
            response = await client.get(api_url)
            
            if response.status_code == 200:
                data = response.json()
                for job in data.get("jobs", []):
                    # Parse HTML content to plain text
                    content_html = job.get("content", "")
                    description = ""
                    if content_html:
                        from html import unescape
                        content_html = unescape(content_html)
                        soup = BeautifulSoup(content_html, 'html.parser')
                        description = soup.get_text(separator='\n', strip=True)
                    
                    jobs.append({
                        "job_id": f"gh_{company}_{job.get('id')}",
                        "greenhouse_id": job.get("id"),
                        "title": job.get("title"),
                        "company": company.replace("-", " ").title(),
                        "company_slug": company,
                        "location": job.get("location", {}).get("name", ""),
                        "department": job.get("departments", [{}])[0].get("name", "") if job.get("departments") else "",
                        "employment_type": job.get("employment_type", "FULLTIME"),
                        "apply_link": job.get("absolute_url"),
                        "posted_at": job.get("updated_at"),
                        "description": description,
                        "source": "greenhouse"
                    })
            else:
                logger.debug(f"Greenhouse API returned {response.status_code} for {company}")
                
    except Exception as e:
        logger.error(f"Error fetching Greenhouse jobs for {company}: {str(e)}")
    
    return jobs

async def fetch_greenhouse_job_details(company: str, job_id: int) -> Optional[Dict]:
    """Fetch detailed job description from Greenhouse."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            api_url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs/{job_id}"
            response = await client.get(api_url)
            
            if response.status_code == 200:
                data = response.json()
                # Parse HTML content to plain text
                content_html = data.get("content", "")
                if content_html:
                    soup = BeautifulSoup(content_html, 'html.parser')
                    description = soup.get_text(separator='\n', strip=True)
                else:
                    description = ""
                
                return {
                    "description": description,
                    "full_description": description,
                    "requirements": data.get("requirements", ""),
                    "departments": [d.get("name") for d in data.get("departments", [])],
                    "offices": [o.get("name") for o in data.get("offices", [])],
                    "metadata": data.get("metadata", [])
                }
    except Exception as e:
        logger.error(f"Error fetching Greenhouse job details: {str(e)}")
    
    return None

async def fetch_lever_company_jobs(company: str) -> List[Dict]:
    """Fetch job listings from a Lever company board."""
    jobs = []
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            api_url = f"https://api.lever.co/v0/postings/{company}"
            response = await client.get(api_url)
            
            if response.status_code == 200:
                data = response.json()
                for job in data:
                    # Lever provides descriptionPlain for full text description
                    description = job.get("descriptionPlain", "")
                    if not description:
                        # Fallback: parse HTML description
                        desc_html = job.get("description", "")
                        if desc_html:
                            soup = BeautifulSoup(desc_html, 'html.parser')
                            description = soup.get_text(separator='\n', strip=True)
                    
                    # Also get lists (requirements, responsibilities, etc.)
                    for lst in job.get("lists", []):
                        list_title = lst.get("text", "")
                        list_content = lst.get("content", "")
                        if list_content:
                            soup = BeautifulSoup(list_content, 'html.parser')
                            list_text = soup.get_text(separator='\n', strip=True)
                            description += f"\n\n{list_title}\n{list_text}"
                    
                    jobs.append({
                        "job_id": f"lv_{company}_{job.get('id')}",
                        "lever_id": job.get("id"),
                        "title": job.get("text"),
                        "company": company.replace("-", " ").title(),
                        "company_slug": company,
                        "location": job.get("categories", {}).get("location", ""),
                        "department": job.get("categories", {}).get("team", ""),
                        "employment_type": job.get("categories", {}).get("commitment", "Full-time"),
                        "apply_link": job.get("hostedUrl") or job.get("applyUrl"),
                        "posted_at": job.get("createdAt"),
                        "description": description.strip(),
                        "source": "lever"
                    })
            else:
                logger.debug(f"Lever API returned {response.status_code} for {company}")
                
    except httpx.TimeoutException:
        logger.debug(f"Timeout fetching Lever jobs for {company}")
    except Exception as e:
        logger.debug(f"Error fetching Lever jobs for {company}: {type(e).__name__}")
    
    return jobs

async def fetch_ashby_company_jobs(company: str) -> List[Dict]:
    """Fetch job listings from an Ashby company board."""
    jobs = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Ashby uses jobs.ashbyhq.com/{company}
            api_url = f"https://jobs.ashbyhq.com/{company}"
            response = await client.get(api_url)
            
            if response.status_code == 200:
                # Ashby embeds job data in the HTML page
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all job postings (Ashby uses specific class names)
                job_elements = soup.find_all('a', class_='ashby-job-posting-brief-list__list-item')
                
                for job_elem in job_elements:
                    try:
                        title = job_elem.find('h3').get_text(strip=True) if job_elem.find('h3') else ""
                        location_elem = job_elem.find('div', class_='ashby-job-posting-brief-list__list-item-location')
                        location = location_elem.get_text(strip=True) if location_elem else ""
                        job_link = job_elem.get('href', '')
                        
                        if not job_link.startswith('http'):
                            job_link = f"https://jobs.ashbyhq.com{job_link}"
                        
                        # Extract job ID from URL
                        job_id = job_link.split('/')[-1] if job_link else ""
                        
                        jobs.append({
                            "job_id": f"ab_{company}_{job_id}",
                            "ashby_id": job_id,
                            "title": title,
                            "company": company.replace("-", " ").title(),
                            "company_slug": company,
                            "location": location,
                            "department": "",
                            "employment_type": "FULLTIME",
                            "apply_link": job_link,
                            "posted_at": "",
                            "source": "ashby"
                        })
                    except Exception as e:
                        logger.debug(f"Error parsing Ashby job element: {e}")
                        continue
            else:
                logger.debug(f"Ashby returned {response.status_code} for {company}")
                
    except Exception as e:
        logger.error(f"Error fetching Ashby jobs for {company}: {str(e)}")
    
    return jobs


async def fetch_amazon_jobs(max_pages: int = 5, countries: List[str] = None) -> List[Dict]:
    """Fetch job listings from Amazon's careers API for multiple countries."""
    if countries is None:
        countries = ["USA", "CAN"]  # Include USA and Canada by default
    
    jobs = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            for country in countries:
                for page in range(max_pages):
                    offset = page * 25
                    api_url = "https://www.amazon.jobs/en/search.json"
                    params = {
                        "base_query": "",
                        "result_limit": 25,
                        "sort": "recent",
                        "offset": offset,
                        "country": country,
                    }
                    response = await client.get(api_url, params=params, headers={"User-Agent": "Mozilla/5.0"})
                    
                    if response.status_code != 200:
                        logger.debug(f"Amazon API returned {response.status_code} for {country}")
                        break
                    
                    data = response.json()
                    page_jobs = data.get("jobs", [])
                    if not page_jobs:
                        break
                    
                    for j in page_jobs:
                        title = j.get("title", "")
                        if not is_english_job(title):
                            continue
                        
                        job_id_raw = j.get("id_icims") or j.get("id", "")
                        apply_link = j.get("url_next_step") or f"https://www.amazon.jobs/en/jobs/{job_id_raw}"
                        
                        jobs.append({
                            "job_id": f"amz_{job_id_raw}",
                            "title": title,
                            "company": "Amazon",
                            "company_slug": "amazon",
                            "location": j.get("location", ""),
                            "department": j.get("job_category", ""),
                            "employment_type": j.get("job_schedule_type", "full-time").upper().replace("-", ""),
                            "apply_link": apply_link,
                            "posted_at": j.get("posted_date", ""),
                            "description": j.get("description", "") or j.get("description_short", ""),
                            "source": "amazon",
                        })
                    
                    if len(page_jobs) < 25:
                        break
                
                logger.info(f"Fetched {len([j for j in jobs if country.lower() in j.get('location', '').lower() or (country == 'CAN' and 'canada' in j.get('location', '').lower())])} Amazon jobs from {country}")
        
        logger.info(f"Fetched {len(jobs)} total Amazon jobs (USA + Canada)")
    except Exception as e:
        logger.error(f"Error fetching Amazon jobs: {e}")
    
    return jobs


async def fetch_company_jobs_via_jsearch(company_name: str, max_results: int = 50, countries: List[str] = None) -> List[Dict]:
    """Fetch jobs for a specific company using JSearch API (for companies without public APIs).
    
    Args:
        company_name: Name of the company to search for
        max_results: Maximum number of results per country
        countries: List of country codes (e.g., ["US", "CA"]). Default is US and Canada.
    """
    if not RAPIDAPI_KEY:
        logger.debug(f"No RapidAPI key, skipping JSearch fetch for {company_name}")
        return []
    
    if countries is None:
        countries = ["US", "CA"]  # Include USA and Canada by default
    
    jobs = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            headers = {
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
            }
            
            for country in countries:
                # Use country-specific queries for better results
                if country == "CA":
                    query = f"{company_name} jobs Canada"
                else:
                    query = f"{company_name} jobs"
                
                params = {
                    "query": query,
                    "num_pages": 2,
                    "page": 1,
                    "employment_types": "FULLTIME",
                    "company_types": "Large",
                }
                
                # Add country filter if supported
                if country:
                    params["country"] = country
                
                response = await client.get(
                    "https://jsearch.p.rapidapi.com/search",
                    headers=headers,
                    params=params,
                )
                
                if response.status_code != 200:
                    logger.debug(f"JSearch returned {response.status_code} for {company_name} in {country}")
                    continue
                
                data = response.json()
                results = data.get("data", [])
                
                country_jobs_count = 0
                for j in results:
                    employer = j.get("employer_name", "")
                    if company_name.lower() not in employer.lower():
                        continue
                    
                    apply_link = j.get("job_apply_link", "")
                    if any(d in apply_link.lower() for d in ["bebee.com", "talent.com", "indeed.com"]):
                        continue
                    
                    title = j.get("job_title", "")
                    if not is_english_job(title):
                        continue
                    
                    job_id = j.get("job_id", "")
                    slug = company_name.lower().replace(" ", "")
                    
                    # Build location string
                    location_parts = [
                        j.get('job_city', ''),
                        j.get('job_state', ''),
                        j.get('job_country', '')
                    ]
                    location = ", ".join([p for p in location_parts if p]).strip(", ")
                    
                    jobs.append({
                        "job_id": f"js_{slug}_{job_id}",
                        "title": title,
                        "company": employer,
                        "company_slug": slug,
                        "location": location,
                        "department": "",
                        "employment_type": j.get("job_employment_type", "FULLTIME"),
                        "apply_link": apply_link,
                        "posted_at": j.get("job_posted_at_datetime_utc", ""),
                        "description": j.get("job_description", "") or "",
                        "source": "jsearch",
                    })
                    country_jobs_count += 1
                
                logger.info(f"Fetched {country_jobs_count} {company_name} jobs from {country} via JSearch")
        
        logger.info(f"Fetched {len(jobs)} total {company_name} jobs via JSearch (all countries)")
    except Exception as e:
        logger.error(f"Error fetching {company_name} jobs via JSearch: {e}")
    
    return jobs


async def cleanup_expired_jobs(days_old: int = 30):
    """Remove expired/stale job listings older than the specified number of days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_old)
    try:
        result = await db.stored_jobs.delete_many({
            "$or": [
                {"last_updated": {"$lt": cutoff}},
                {"ingested_at": {"$lt": cutoff}, "last_updated": {"$exists": False}},
            ]
        })
        logger.info(f"Cleaned up {result.deleted_count} expired jobs (older than {days_old} days)")
        return result.deleted_count
    except Exception as e:
        logger.error(f"Error cleaning up expired jobs: {e}")
        return 0


# ========================
# PARALLEL BATCH FETCHING & CACHING
# ========================

async def fetch_all_jobs_parallel() -> List[Dict]:
    """Fetch jobs from all platforms in parallel batches for speed."""
    all_jobs = []
    
    # Prepare all fetch tasks for Greenhouse and Lever
    tasks = []
    for company in GREENHOUSE_COMPANIES:
        tasks.append(("greenhouse", company, fetch_greenhouse_company_jobs(company)))
    for company in LEVER_COMPANIES:
        tasks.append(("lever", company, fetch_lever_company_jobs(company)))
    # Skip Ashby for now - requires Playwright
    
    logger.info(f"Fetching from {len(tasks)} Greenhouse/Lever companies in parallel...")
    start_time = datetime.now(timezone.utc)
    
    # Process Greenhouse/Lever in batches for controlled parallelism
    batch_size = PARALLEL_BATCH_SIZE
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i + batch_size]
        batch_coros = [t[2] for t in batch]
        
        results = await asyncio.gather(*batch_coros, return_exceptions=True)
        
        for j, result in enumerate(results):
            platform, company, _ = batch[j]
            if isinstance(result, list) and result:
                all_jobs.extend(result)
                logger.debug(f"  {platform}/{company}: {len(result)} jobs")
            elif isinstance(result, Exception):
                logger.debug(f"  {platform}/{company}: error - {type(result).__name__}")
    
    # Fetch from new ATS platforms (SmartRecruiters, Pinpoint)
    try:
        logger.info("Fetching from SmartRecruiters and Pinpoint...")
        new_ats_jobs = await fetch_all_new_ats_jobs_flat()
        if new_ats_jobs:
            all_jobs.extend(new_ats_jobs)
            logger.info(f"Added {len(new_ats_jobs)} jobs from SmartRecruiters/Pinpoint")
    except Exception as e:
        logger.error(f"Error fetching from new ATS platforms: {e}")
    
    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
    logger.info(f"Parallel fetch complete: {len(all_jobs)} jobs in {elapsed:.1f}s")
    
    return all_jobs

async def get_cached_jobs(user_id: str) -> Optional[Dict]:
    """Get cached jobs for a user if still valid."""
    cache = await db.job_cache.find_one({"user_id": user_id})
    if cache:
        cached_at = cache.get("cached_at")
        if cached_at:
            age_minutes = (datetime.now(timezone.utc) - cached_at).total_seconds() / 60
            if age_minutes < JOB_CACHE_TTL_MINUTES:
                return cache
    return None

async def save_jobs_to_cache(user_id: str, jobs: List[Dict], query: str, location: str):
    """Save fetched jobs to user's cache."""
    # Get existing job IDs to detect new jobs later
    existing_cache = await db.job_cache.find_one({"user_id": user_id})
    existing_job_ids = set()
    if existing_cache:
        existing_job_ids = set(j.get("job_id") for j in existing_cache.get("jobs", []))
    
    # Mark new jobs
    for job in jobs:
        job["is_new_for_user"] = job.get("job_id") not in existing_job_ids
    
    await db.job_cache.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "user_id": user_id,
                "jobs": jobs,
                "query": query,
                "location": location,
                "cached_at": datetime.now(timezone.utc),
                "total_jobs": len(jobs)
            }
        },
        upsert=True
    )
    
    # Also save to user's saved jobs collection for dashboard
    await db.user_saved_jobs.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "user_id": user_id,
                "jobs": jobs[:50],  # Keep top 50 for dashboard
                "last_search_query": query,
                "last_search_location": location,
                "updated_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )
    
    new_count = sum(1 for j in jobs if j.get("is_new_for_user"))
    logger.info(f"Saved {len(jobs)} jobs to cache for user {user_id} ({new_count} new)")

async def search_greenhouse_jobs(query: str = "", location: str = "", limit: int = 50) -> List[Dict]:
    """Search for jobs across multiple Greenhouse company boards."""
    all_jobs = []
    query_words = query.lower().split() if query else []
    location_lower = location.lower() if location else ""
    
    logger.info(f"Searching Greenhouse: query_words={query_words}, location={location_lower}")
    
    # Fetch jobs from multiple companies in parallel
    tasks = [fetch_greenhouse_company_jobs(company) for company in GREENHOUSE_COMPANIES]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    success_count = 0
    for result in results:
        if isinstance(result, list):
            all_jobs.extend(result)
            success_count += 1
        elif isinstance(result, Exception):
            logger.debug(f"Greenhouse fetch error: {result}")
    
    logger.info(f"Greenhouse: fetched from {success_count} companies, total {len(all_jobs)} jobs")
    
    # Filter by query and location with synonym expansion
    expanded_phrases = expand_query(query) if query else []
    filtered_jobs = []
    for job in all_jobs:
        job_title = (job.get("title") or "").lower()
        job_company = (job.get("company") or "").lower()
        job_dept = (job.get("department") or "").lower()
        job_location = (job.get("location") or "").lower()
        search_text = f"{job_title} {job_company} {job_dept}"
        
        # Match query - any word must match title, company, or department + synonym expansion
        query_match = not query_words or any(
            word in job_title or word in job_company or word in job_dept
            for word in query_words
        ) or any(syn in job_title for syn in expanded_phrases)
        
        # Match location
        location_match = not location_lower or location_lower in job_location
        
        if query_match and location_match:
            filtered_jobs.append(job)
    
    # Sort by posted date (most recent first)
    filtered_jobs.sort(key=lambda x: x.get("posted_at", ""), reverse=True)
    
    return filtered_jobs[:limit]

async def enrich_greenhouse_job(job: Dict, profile: Optional[Dict]) -> Dict:
    """Enrich a Greenhouse job with full description and match scoring."""
    # Fetch full job details
    if job.get("greenhouse_id") and job.get("company_slug"):
        details = await fetch_greenhouse_job_details(job["company_slug"], job["greenhouse_id"])
        if details:
            job["description"] = details.get("description", "")[:500] + "..."
            job["full_description"] = details.get("description", "")
    
    # Calculate match score
    if profile:
        # Create a job dict compatible with evaluate_job_match
        job_for_match = {
            "job_title": job.get("title"),
            "employer_name": job.get("company"),
            "job_description": job.get("full_description", job.get("description", "")),
            "job_city": job.get("location", "").split(",")[0].strip() if job.get("location") else "",
            "job_state": job.get("location", "").split(",")[-1].strip() if "," in job.get("location", "") else "",
            "job_is_remote": "remote" in job.get("location", "").lower(),
            "job_min_salary": None,
            "job_max_salary": None
        }
        match_eval = evaluate_job_match(job_for_match, profile)
        job.update({
            "match_score": match_eval["score"],
            "match_recommendation": match_eval["recommendation"],
            "match_strengths": match_eval["strengths"],
            "match_gaps": match_eval["gaps"],
            "match_reasoning": match_eval["match_reasoning"],
            "skip_reason": match_eval["skip_reason"],
            "grounded_strengths": match_eval.get("grounded_strengths", []),
            "matched_skills": match_eval.get("matched_skills", [])
        })
    else:
        job.update({
            "match_score": 50,
            "match_recommendation": "review",
            "match_strengths": [],
            "match_gaps": ["Complete your profile for better matching"],
            "match_reasoning": "Profile incomplete",
            "skip_reason": None,
            "grounded_strengths": [],
            "matched_skills": []
        })
    
    return job

@router.post("/jobs/greenhouse/search")
async def search_greenhouse(request: Request):
    """Search for jobs from Greenhouse, Lever, and Ashby-powered career pages with streaming."""
    logger.info("=== GREENHOUSE SEARCH ENDPOINT CALLED ===")
    user = await get_current_user(request)
    logger.info(f"User authenticated: {user.user_id}")
    
    body = await request.json()
    query = body.get("query", "")
    location = body.get("location", "")
    is_fallback = body.get("fallback_search", False)
    company_filter = body.get("company", "").strip()
    
    logger.info(f"Multi-platform job search (streaming): query='{query}', location='{location}', company='{company_filter}', fallback={is_fallback}")
    
    # Get user profile for matching and intensity filtering
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    # Get application intensity setting (default: balanced)
    intensity = profile.get("application_intensity", "balanced") if profile else "balanced"
    
    # ALL PROFILE-BASED FILTERING DISABLED
    # We only filter by title/location search terms
    # Match scores are calculated for ranking but NOT used to filter
    # User decides which jobs to apply to based on match scores displayed
    min_match_score = 0
    
    logger.info(f"Search mode: Show ALL jobs matching query/location. Match scoring enabled for ranking (no filtering).")
    
    # Get applied job IDs to filter duplicates
    existing_applications = await db.applications.find(
        {"user_id": user.user_id},
        {"job_id": 1, "_id": 0}
    ).to_list(500)
    applied_job_ids = set(app.get("job_id") for app in existing_applications if app.get("job_id"))
    
    async def stream_multi_platform_jobs():
        """Generator function that streams jobs from all platforms using parallel fetching."""
        logger.info("=== STREAMING FUNCTION STARTED (PARALLEL MODE) ===")
        import json
        
        # Send immediate heartbeat so frontend knows we're alive
        yield f"data: {json.dumps({'heartbeat': True, 'message': 'Search started - fetching from quality sources...'})}\n\n"
        
        query_words = query.lower().split() if query else []
        location_lower = location.lower() if location else ""
        is_fallback_search = body.get("fallback_search", False)
        
        jobs_found = 0
        matched_jobs = []
        skipped_applied = 0
        skipped_non_english = 0
        
        # PARALLEL FETCH: Get all jobs at once (much faster than sequential)
        total_companies = len(GREENHOUSE_COMPANIES) + len(LEVER_COMPANIES)
        yield f"data: {json.dumps({'progress': True, 'message': f'Scanning {total_companies} companies...', 'checked': 0, 'found': 0})}\n\n"
        
        # Fetch all jobs in parallel batches
        all_raw_jobs = await fetch_all_jobs_parallel()
        
        yield f"data: {json.dumps({'progress': True, 'message': f'Found {len(all_raw_jobs)} total jobs, filtering...', 'checked': total_companies, 'found': len(all_raw_jobs)})}\n\n"
        
        # Get existing job IDs from user's previous search (to mark new jobs)
        existing_cache = await db.job_cache.find_one({"user_id": user.user_id})
        existing_job_ids = set()
        if existing_cache:
            existing_job_ids = set(j.get("job_id") for j in existing_cache.get("jobs", []))
        
        # Filter and process jobs
        expanded_phrases = expand_query(query) if query else []
        
        for job in all_raw_jobs:
            # Skip already applied jobs
            if job.get("job_id") in applied_job_ids:
                skipped_applied += 1
                continue
            
            # Skip non-English job postings
            if not is_english_job(job.get("title", "")):
                skipped_non_english += 1
                continue
            
            # Apply company filter if specified
            if company_filter:
                job_company_name = (job.get("company") or "").lower()
                company_filter_lower = company_filter.lower()
                if company_filter_lower not in job_company_name and job_company_name not in company_filter_lower:
                    continue
            
            job_title = (job.get("title") or "").lower()
            job_company = (job.get("company") or "").lower()
            job_dept = (job.get("department") or "").lower()
            job_location = (job.get("location") or "").lower()
            search_text = f"{job_title} {job_company} {job_dept}"
            
            # Query match logic with synonym expansion
            query_match = True
            if query_words:
                if len(query_words) >= 2:
                    if is_fallback_search:
                        # FALLBACK MODE: Any keyword match
                        query_match = any(word in search_text for word in query_words)
                    else:
                        # BALANCED MODE: phrase match OR synonym match OR most words match
                        query_phrase = query.lower()
                        # Significant words are 4+ chars (skip "in", "of", "the", etc.)
                        significant_words = [w for w in query_words if len(w) >= 4]
                        query_match = (
                            query_phrase in job_title or
                            all(word in job_title for word in query_words) or
                            query_phrase in search_text or
                            sum(1 for word in query_words if word in search_text) >= 2 or
                            any(syn in job_title for syn in expanded_phrases) or
                            (significant_words and all(w in search_text for w in significant_words))
                        )
                else:
                    # Single word - broad matching
                    query_match = any(word in search_text for word in query_words)
            
            if not query_match:
                continue
            
            # Location match logic using comprehensive location parsing
            location_match = True
            if location_lower:
                # Extract user's city and province from search
                user_city = None
                user_province = None
                for city, prov in CANADIAN_CITIES.items():
                    if city in location_lower:
                        user_city = city
                        user_province = prov
                        break
                if not user_province:
                    for prov_name, prov_code in CANADIAN_PROVINCES.items():
                        if len(prov_name) > 2 and prov_name in location_lower:
                            user_province = prov_code
                            break
                
                # Check if this is a Canadian search
                is_canada_search = user_city or user_province or "canada" in location_lower
                
                if is_canada_search:
                    # Parse the job location
                    parsed = parse_location(job.get("location", ""))
                    
                    # Check if valid for Canadian search
                    is_valid, reason = is_job_valid_for_canadian_search(
                        parsed,
                        user_city=user_city,
                        user_province=user_province
                    )
                    
                    location_match = is_valid
                    
                    if is_valid:
                        # Add parsed location info to job
                        job["parsed_location"] = parsed
                        job["remote_label"] = get_remote_label_for_display(parsed)
                        job["location_filter_reason"] = reason
                else:
                    # Non-Canadian search - use simple keyword matching
                    location_words = location_lower.replace(",", " ").split()
                    location_keywords = [w for w in location_words if w not in ["area", "greater", "the", "of", "in"]]
                    location_match = any(keyword in job_location for keyword in location_keywords) if location_keywords else True
            
            if not location_match:
                continue
            
            # Mark if this is a NEW job for the user
            job["is_new_for_user"] = job.get("job_id") not in existing_job_ids
            
            # Calculate match score
            if profile:
                job_for_match = {
                    "job_title": job.get("title"),
                    "employer_name": job.get("company"),
                    "job_description": job.get("description") or ((job.get("title") or "") + " " + (job.get("department") or "")),
                    "job_city": job.get("location", "").split(",")[0].strip() if job.get("location") else "",
                    "job_state": job.get("location", "").split(",")[-1].strip() if "," in job.get("location", "") else "",
                    "job_is_remote": "remote" in job.get("location", "").lower(),
                    "job_min_salary": None,
                    "job_max_salary": None
                }
                match_eval = evaluate_job_match(job_for_match, profile)
                job.update({
                    "match_score": match_eval["score"],
                    "match_recommendation": match_eval["recommendation"],
                    "match_strengths": match_eval["strengths"],
                    "match_gaps": match_eval["gaps"],
                    "match_reasoning": match_eval["match_reasoning"],
                    "skip_reason": match_eval["skip_reason"],
                    "grounded_strengths": match_eval.get("grounded_strengths", []),
                    "matched_skills": match_eval.get("matched_skills", [])
                })
            else:
                job.update({
                    "match_score": 50,
                    "match_recommendation": "review",
                    "match_strengths": [],
                    "match_gaps": ["Complete your profile for better matching"],
                    "match_reasoning": "Profile incomplete",
                    "skip_reason": None,
                    "grounded_strengths": [],
                    "matched_skills": []
                })
            
            # Preserve original description or create fallback summary
            if not job.get("description"):
                job["description"] = f"{job.get('title', '')} position at {job.get('company', '')} in {job.get('location', 'Unknown location')}"
            # full_description for backwards compatibility with frontend
            job["full_description"] = job.get("description", "")
            
            # Mark as new if posted in last 24 hours
            job_posted_date = job.get("posted_at")
            is_new = False
            if job_posted_date:
                try:
                    posted_dt = datetime.fromisoformat(job_posted_date.replace('Z', '+00:00'))
                    hours_ago = (datetime.now(timezone.utc) - posted_dt).total_seconds() / 3600
                    is_new = hours_ago <= 24
                except:
                    is_new = False
            job["is_new"] = is_new
            
            matched_jobs.append(job)
            jobs_found += 1
            
            # Limit to 100 jobs
            if jobs_found >= 100:
                break
        
        logger.info(f"Search complete: {jobs_found} jobs matched from {len(all_raw_jobs)} total")
        
        # Normalize all posted_at to proper datetimes for reliable sorting
        EPOCH = datetime(2000, 1, 1, tzinfo=timezone.utc)
        for job in matched_jobs:
            sort_dt = normalize_posted_date(job.get("posted_at"), fallback=EPOCH)
            job["_sort_dt"] = sort_dt
            # Ensure posted_at is a consistent ISO string for the frontend
            if sort_dt and sort_dt != EPOCH:
                job["posted_at"] = sort_dt.isoformat()
            else:
                job["posted_at"] = ""
        
        # Sort strictly by posted_at descending (newest first)
        matched_jobs.sort(key=lambda x: x.get("_sort_dt") or EPOCH, reverse=True)
        
        # Remove temp sort field before streaming
        for job in matched_jobs:
            job.pop("_sort_dt", None)
        
        # Now stream the sorted jobs
        for job in matched_jobs:
            yield f"data: {json.dumps(job)}\n\n"
        
        # Save jobs to cache for dashboard
        if matched_jobs:
            await save_jobs_to_cache(user.user_id, matched_jobs, query, location)
        
        # Send completion message
        completion_data = {'done': True, 'total': jobs_found}
        
        # Count new jobs
        new_jobs_count = sum(1 for j in matched_jobs if j.get("is_new_for_user"))
        completion_data['new_jobs_count'] = new_jobs_count
        
        # If 0 results for a multi-word query, suggest fallback
        if jobs_found == 0 and len(query_words) >= 2 and not is_fallback_search:
            completion_data['suggest_fallback'] = True
            completion_data['fallback_message'] = f"No exact '{query}' jobs found in {location or 'your area'}. Try showing related roles?"
            completion_data['original_query'] = query
        
        yield f"data: {json.dumps(completion_data)}\n\n"
    
    return StreamingResponse(
        stream_multi_platform_jobs(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@router.get("/jobs/saved")
async def get_saved_jobs(request: Request):
    """Get user's saved jobs from their last search (for dashboard display)."""
    user = await get_current_user(request)
    
    saved = await db.user_saved_jobs.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    if not saved:
        return {
            "jobs": [],
            "last_search_query": None,
            "last_search_location": None,
            "updated_at": None,
            "total": 0
        }
    
    # Define priority ATS sources (jobs from these appear first)
    priority_sources = {"greenhouse", "lever", "ashby", "amazon", "jsearch"}
    
    jobs = saved.get("jobs", [])
    
    # Sort by most recent first
    jobs.sort(key=lambda x: x.get("posted_at") or "1970-01-01", reverse=True)
    
    return {
        "jobs": jobs,
        "last_search_query": saved.get("last_search_query"),
        "last_search_location": saved.get("last_search_location"),
        "updated_at": saved.get("updated_at").isoformat() if saved.get("updated_at") else None,
        "total": len(jobs)
    }

@router.get("/jobs/greenhouse/companies")
async def get_greenhouse_companies(request: Request):
    """Get list of known Greenhouse company boards."""
    await get_current_user(request)
    return {"companies": GREENHOUSE_COMPANIES}

@router.post("/jobs/greenhouse/add-company")
async def add_greenhouse_company(request: Request):
    """Add a new company to the Greenhouse search list."""
    await get_current_user(request)
    body = await request.json()
    company = body.get("company", "").lower().strip()
    
    if not company:
        raise HTTPException(status_code=400, detail="Company name required")
    
    # Validate that the company has a Greenhouse board
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            api_url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
            response = await client.get(api_url)
            
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail=f"No Greenhouse board found for '{company}'")
            
            data = response.json()
            job_count = len(data.get("jobs", []))
            
            if company not in GREENHOUSE_COMPANIES:
                GREENHOUSE_COMPANIES.append(company)
            
            return {
                "message": f"Added {company} with {job_count} jobs",
                "company": company,
                "job_count": job_count
            }
        except httpx.RequestError:
            raise HTTPException(status_code=400, detail=f"Could not verify Greenhouse board for '{company}'")

@router.post("/jobs/search")
async def search_jobs(request: Request):
    """Search for jobs using JSearch API - includes LinkedIn, Indeed, Glassdoor, etc."""
    user = await get_current_user(request)
    
    body = await request.json()
    query = body.get("query", "")
    location = body.get("location", "")
    linkedin_only = body.get("linkedin_only", False)
    company_filter = body.get("company", "").strip()
    
    # Get user profile to determine country preference
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    # Determine country code from user's location preference or search location
    country_code = None
    location_lower = location.lower() if location else ""
    
    # Map common location terms to country codes
    canada_keywords = ["canada", "toronto", "vancouver", "montreal", "ottawa", "calgary", "edmonton", "ontario", "bc", "quebec", "alberta"]
    us_keywords = ["usa", "united states", "new york", "california", "texas", "florida", "seattle", "san francisco", "los angeles", "chicago"]
    uk_keywords = ["uk", "united kingdom", "london", "manchester", "birmingham", "england", "scotland"]
    
    if any(kw in location_lower for kw in canada_keywords):
        country_code = "CA"
    elif any(kw in location_lower for kw in us_keywords):
        country_code = "US"
    elif any(kw in location_lower for kw in uk_keywords):
        country_code = "GB"
    elif profile:
        # Fallback to user's profile location preference
        preferred_locations = profile.get("preferred_locations", [])
        for loc in preferred_locations:
            loc_lower = loc.lower()
            if any(kw in loc_lower for kw in canada_keywords):
                country_code = "CA"
                break
            elif any(kw in loc_lower for kw in us_keywords):
                country_code = "US"
                break
            elif any(kw in loc_lower for kw in uk_keywords):
                country_code = "GB"
                break
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {
                "query": f"{query} {company_filter} {location}".strip() if company_filter else f"{query} {location}".strip(),
                "num_pages": "3" if country_code else ("2" if linkedin_only else "1"),
                "page": "1"
            }
            
            # Add country filter if we determined a country
            if country_code:
                params["country"] = country_code
                logger.info(f"JSearch filtering by country: {country_code}")
            
            response = await client.get(
                "https://jsearch.p.rapidapi.com/search",
                params=params,
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"JSearch API error: {response.status_code}")
                return {"jobs": [], "total": 0}
            
            data = response.json()
            jobs = data.get("data", [])
            
            # Filter out Bebee, Talent.com, and Indeed jobs (require separate login)
            jobs = [job for job in jobs if not any(domain in job.get("job_apply_link", "").lower() for domain in ["bebee.com", "talent.com", "indeed.com"])]
            
            # Apply company filter if specified
            if company_filter:
                company_filter_lower = company_filter.lower()
                jobs = [job for job in jobs if company_filter_lower in (job.get("employer_name", "") or "").lower()]
            
            # Extract user's city and province for location filtering
            user_city = None
            user_province = None
            if location_lower:
                # Parse the search location to get city/province
                for city, prov in CANADIAN_CITIES.items():
                    if city in location_lower:
                        user_city = city
                        user_province = prov
                        break
                if not user_province:
                    for prov_name, prov_code in CANADIAN_PROVINCES.items():
                        if len(prov_name) > 2 and prov_name in location_lower:
                            user_province = prov_code
                            break
            
            # Filter jobs using comprehensive location parsing
            if country_code == "CA":
                filtered_jobs = []
                
                for job in jobs:
                    job_location = job.get("job_city", "") or ""
                    if job.get("job_state"):
                        job_location += f", {job.get('job_state')}"
                    if job.get("job_country"):
                        job_location += f", {job.get('job_country')}"
                    
                    # Also check the job employment type for remote indicators
                    is_remote = job.get("job_is_remote", False)
                    if is_remote:
                        job_location = f"Remote - {job_location}" if job_location else "Remote"
                    
                    # Parse the location
                    parsed = parse_location(
                        job_location,
                        job_country=job.get("job_country", ""),
                        job_state=job.get("job_state", ""),
                        job_city=job.get("job_city", "")
                    )
                    
                    # Check if valid for Canadian search
                    is_valid, reason = is_job_valid_for_canadian_search(
                        parsed, 
                        user_city=user_city,
                        user_province=user_province
                    )
                    
                    if is_valid:
                        # Add parsed location info to job
                        job["parsed_location"] = parsed
                        job["remote_label"] = get_remote_label_for_display(parsed)
                        job["location_filter_reason"] = reason
                        filtered_jobs.append(job)
                    else:
                        logger.debug(f"Filtered out job: {job.get('job_title')} - {reason}")
                
                logger.info(f"Location filter: {len(jobs)} -> {len(filtered_jobs)} jobs for {user_city or user_province or 'Canada'}")
                jobs = filtered_jobs
            
            # Filter for LinkedIn only if requested
            if linkedin_only:
                jobs = [job for job in jobs if "linkedin.com" in job.get("job_apply_link", "").lower()]
                logger.info(f"Filtered to {len(jobs)} LinkedIn jobs")
            else:
                logger.info(f"Filtered to {len(jobs)} jobs")
            
            # Get applied job IDs to filter duplicates
            existing_applications = await db.applications.find(
                {"user_id": user.user_id},
                {"job_id": 1, "_id": 0}
            ).to_list(500)
            applied_job_ids = set(app.get("job_id") for app in existing_applications if app.get("job_id"))
            
            # Filter out already applied jobs (KEEP LinkedIn this time)
            jobs = [job for job in jobs if job.get("job_id") not in applied_job_ids]
            
            # Enrich jobs with match evaluation
            enriched_jobs = []
            for job in jobs[:30]:
                if profile:
                    match_eval = evaluate_job_match(job, profile)
                    job.update({
                        "match_score": match_eval["score"],
                        "match_recommendation": match_eval["recommendation"],
                        "match_strengths": match_eval["strengths"],
                        "match_gaps": match_eval["gaps"],
                        "match_reasoning": match_eval["match_reasoning"],
                        "skip_reason": match_eval["skip_reason"],
                        "grounded_strengths": match_eval.get("grounded_strengths", []),
                        "matched_skills": match_eval.get("matched_skills", [])
                    })
                else:
                    job.update({
                        "match_score": 50,
                        "match_recommendation": "review",
                        "match_strengths": [],
                        "match_gaps": ["Complete your profile for better matching"],
                        "match_reasoning": "Profile incomplete",
                        "skip_reason": None,
                        "grounded_strengths": [],
                        "matched_skills": []
                    })
                
                # Transform to match our format
                job_posted_date = job.get("job_posted_at_datetime_utc")
                is_new = False
                if job_posted_date:
                    try:
                        from datetime import datetime, timezone
                        posted_dt = datetime.fromisoformat(job_posted_date.replace('Z', '+00:00'))
                        hours_ago = (datetime.now(timezone.utc) - posted_dt).total_seconds() / 3600
                        is_new = hours_ago <= 24  # New if posted in last 24 hours
                    except:
                        is_new = False
                
                enriched_jobs.append({
                    "job_id": job.get("job_id"),
                    "title": job.get("job_title"),
                    "company": job.get("employer_name"),
                    "location": f"{job.get('job_city', '')}, {job.get('job_state', '')}".strip(", "),
                    "employment_type": job.get("job_employment_type"),
                    "description": job.get("job_description", "")[:500] + "..." if job.get("job_description") else "",
                    "apply_link": job.get("job_apply_link"),
                    "posted_at": job_posted_date,
                    "is_new": is_new,
                    "source": "aggregator",
                    "is_linkedin": "linkedin.com" in job.get("job_apply_link", "").lower(),
                    "requires_login": "linkedin.com" in job.get("job_apply_link", "").lower(),
                    "match_score": job.get("match_score"),
                    "match_recommendation": job.get("match_recommendation"),
                    "match_strengths": job.get("match_strengths"),
                    "match_gaps": job.get("match_gaps"),
                    "match_reasoning": job.get("match_reasoning"),
                    "skip_reason": job.get("skip_reason")
                })
            
            # Sort by posted date (newest first)
            enriched_jobs.sort(key=lambda x: x.get("posted_at") or "", reverse=True)
            
            return {
                "jobs": enriched_jobs,
                "total": len(enriched_jobs)
            }
    except Exception as e:
        logger.error(f"JSearch error: {str(e)}")
        return {"jobs": [], "total": 0}

def evaluate_job_match(job: Dict, profile: Optional[Dict]) -> Dict:
    """
    Evaluate job match to help user decide whether to apply.
    Returns match score, decision summary, strengths, risks, confidence, and recommendation.
    Focus: Guide decision-making with honesty and clarity, not hype.
    Enhanced to provide grounded strengths with actual resume evidence.
    """
    if not profile:
        return {
            "score": 50,
            "recommendation": "review",
            "confidence": "low",
            "risk": "high",
            "decision_summary": "Complete your profile for personalized match analysis",
            "strengths": [],
            "grounded_strengths": [],
            "matched_skills": [],
            "gaps": ["Complete your profile and upload resume for accurate matching"],
            "match_reasoning": "Profile incomplete - unable to provide detailed analysis",
            "skip_reason": None,
            "auto_apply_blocked": True,
            "auto_apply_reason": "Insufficient profile data"
        }
    
    # Extract job details
    job_title = (job.get("job_title") or "").lower()
    job_desc = (job.get("job_description") or "").lower()
    job_title_display = job.get("job_title") or "this role"
    company_name = job.get("employer_name") or "this company"
    job_city = job.get("job_city") or ""
    job_state = job.get("job_state") or ""
    job_location = (job_city + " " + job_state).lower().strip()
    is_remote = job.get("job_is_remote", False)
    
    # Extract profile details
    resume_text_raw = profile.get("resume_text") or ""
    resume_text = resume_text_raw.lower()
    has_resume = len(resume_text) > 100
    target_roles = [r.lower() for r in profile.get("job_titles", [])]
    profile_skills = get_skill_names(profile.get("skills", []))
    user_years = profile.get("experience_years", 0)
    user_seniority = profile.get("seniority_level", "").lower()
    
    # Initialize scoring
    score = 0
    strengths = []
    grounded_strengths = []
    risks = []
    gaps = []
    matched_skills = []
    auto_apply_blocked = False
    auto_apply_reason = None
    
    # ============================================================================
    # HELPER: Extract meaningful resume evidence (not raw text dumps)
    # ============================================================================
    
    # Patterns to filter out (contact info, headers, etc.)
    import re
    FILTER_PATTERNS = [
        r'\b[\w.-]+@[\w.-]+\.\w+\b',  # Email addresses
        r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # Phone numbers
        r'https?://[^\s]+',  # URLs
        r'linkedin\.com[^\s]*',  # LinkedIn
        r'github\.com[^\s]*',  # GitHub
        r'\b(resume|cv|curriculum vitae)\b',  # Resume headers
    ]
    
    def is_meaningful_line(line: str) -> bool:
        """Check if a line contains meaningful content (not contact info/headers)."""
        line_lower = line.lower().strip()
        
        # Skip empty or very short lines
        if len(line_lower) < 15:
            return False
        
        # Skip lines that are mostly contact info
        for pattern in FILTER_PATTERNS:
            if re.search(pattern, line_lower, re.IGNORECASE):
                return False
        
        # Skip lines that look like headers/names (all caps, short)
        if line.isupper() and len(line) < 50:
            return False
        
        # Skip lines with just location/date info
        if re.match(r'^[\w\s,]+\s*\|\s*[\d/\-\s]+$', line_lower):
            return False
        
        return True
    
    def extract_achievement_bullets(resume: str) -> List[str]:
        """Extract meaningful bullet points and achievements from resume."""
        achievements = []
        lines = resume.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for bullet points or lines starting with action verbs
            if line.startswith(('-', '•', '●', '○', '*')) or \
               (len(line) > 20 and any(line.lower().startswith(v) for v in [
                   'led', 'managed', 'developed', 'created', 'built', 'designed',
                   'implemented', 'improved', 'increased', 'decreased', 'reduced',
                   'achieved', 'delivered', 'launched', 'coordinated', 'analyzed',
                   'collaborated', 'established', 'generated', 'optimized', 'spearheaded',
                   'streamlined', 'transformed', 'automated', 'conducted', 'drove'
               ])):
                # Clean the bullet point
                cleaned = re.sub(r'^[-•●○*]\s*', '', line).strip()
                if is_meaningful_line(cleaned) and len(cleaned) > 25:
                    achievements.append(cleaned)
        
        return achievements[:20]  # Limit to top 20
    
    def extract_work_experience(resume: str) -> List[Dict]:
        """Extract work experience entries from resume."""
        experiences = []
        lines = resume.split('\n')
        
        # Title keywords for identifying job titles vs company names
        title_keywords = [
            'engineer', 'developer', 'analyst', 'manager', 'director', 'lead',
            'architect', 'designer', 'specialist', 'coordinator', 'consultant',
            'associate', 'intern', 'officer', 'administrator', 'scientist'
        ]
        # Company indicators
        company_indicators = ['inc', 'corp', 'llc', 'ltd', 'co.', 'technologies',
                            'solutions', 'group', 'labs', 'studio', 'systems']
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue
            
            line_lower = line.lower()
            
            # Look for lines with pipe/dash separators containing dates (common resume format)
            # e.g., "Senior Software Engineer | TechCorp Inc. | Jan 2022 - Present"
            has_date = bool(re.search(r'\b(20\d{2}|19\d{2})\b', line_lower))
            if not has_date:
                continue
            
            parts = re.split(r'\s*[|]\s*', line)
            if len(parts) < 2:
                parts = re.split(r'\s*[-–]\s*(?=[A-Z])', line, maxsplit=1)
            
            if len(parts) >= 2:
                title_part = None
                company_part = None
                
                for part in parts:
                    part_lower = part.strip().lower()
                    # Skip date-only parts
                    if re.match(r'^[\w\s,]*(20\d{2}|19\d{2})[\s\-–]*(present|20\d{2}|19\d{2})?[\s]*$', part_lower):
                        continue
                    # Check if this part looks like a title or a company
                    is_title = any(kw in part_lower for kw in title_keywords)
                    is_company = any(kw in part_lower for kw in company_indicators)
                    
                    if is_title and not title_part:
                        title_part = part.strip()
                    elif is_company and not company_part:
                        company_part = part.strip()
                    elif not title_part and not is_company:
                        title_part = part.strip()
                    elif not company_part:
                        company_part = part.strip()
                
                if title_part and company_part:
                    experiences.append({"company": company_part, "title": title_part})
                elif title_part:
                    experiences.append({"company": None, "title": title_part})
        
        return experiences[:5]
    
    def find_skill_evidence(skill: str, resume: str, achievements: List[str]) -> str:
        """Find meaningful evidence for a skill from resume achievements."""
        skill_lower = skill.lower()
        
        # Search through achievements for skill mentions with context
        for achievement in achievements:
            if skill_lower in achievement.lower():
                # Found an achievement mentioning this skill
                return achievement[:200] + "..." if len(achievement) > 200 else achievement
        
        # Search for skill in resume with surrounding achievement context
        resume_lower = resume.lower()
        idx = resume_lower.find(skill_lower)
        if idx != -1:
            # Get the line containing this skill
            start = resume_lower.rfind('\n', 0, idx)
            end = resume_lower.find('\n', idx)
            if start == -1:
                start = 0
            if end == -1:
                end = len(resume)
            
            line = resume[start:end].strip()
            if is_meaningful_line(line) and len(line) > 30:
                return line[:200] + "..." if len(line) > 200 else line
        
        return ""
    
    # Pre-extract achievements from resume for later use
    resume_achievements = extract_achievement_bullets(resume_text_raw) if has_resume else []
    work_experiences = extract_work_experience(resume_text_raw) if has_resume else []
    
    # ============================================================================
    # CATEGORY 1: CORE FIT (60 points) - Should I apply?
    # ============================================================================
    
    # 1.1 ROLE ALIGNMENT (20 points) - Title synonym mapping
    role_score = 0
    role_matched = False
    
    # Define title synonyms and related roles
    title_synonyms = {
        "business analyst": ["systems analyst", "data analyst", "business systems analyst", "process analyst", 
                            "functional analyst", "requirements analyst", "workday analyst", "analyst"],
        "data analyst": ["business intelligence analyst", "analytics analyst", "reporting analyst", 
                        "business analyst", "data specialist"],
        "software engineer": ["software developer", "engineer", "developer", "programmer", "sde"],
        "product manager": ["product owner", "pm", "product lead", "product specialist"],
        "project manager": ["program manager", "project lead", "delivery manager", "scrum master"],
        "accountant": ["accounting analyst", "financial analyst", "accounting specialist"],
        "marketing": ["marketing specialist", "marketing coordinator", "digital marketing", "marketing analyst"]
    }
    
    # Check target roles against job title
    matched_role = None
    for target_role in target_roles:
        # Direct match
        if target_role in job_title or any(word in job_title for word in target_role.split()):
            role_score = 20
            role_matched = True
            matched_role = target_role.title()
            
            # Find work experience evidence for the role
            relevant_exp = None
            for exp in work_experiences:
                if exp.get("title") and target_role.split()[0].lower() in exp["title"].lower():
                    relevant_exp = exp
                    break
            
            if relevant_exp and relevant_exp.get("company"):
                grounded_strengths.append({
                    "strength_title": f"{matched_role} Experience",
                    "evidence": f"Previously worked as {relevant_exp.get('title', matched_role)} at {relevant_exp['company']}",
                    "relevance": f"Direct role alignment with {job_title_display} position"
                })
            break
        
        # Synonym match
        for category, synonyms in title_synonyms.items():
            if target_role in synonyms or category == target_role:
                if any(syn in job_title for syn in synonyms):
                    role_score = 18
                    role_matched = True
                    matched_role = target_role.title()
                    strengths.append(f"Related role: {job_title_display} aligns with your {matched_role} career path")
                    break
        
        if role_matched:
            break
    
    if not role_matched and target_roles:
        role_score = 5
        risks.append(f"Role title doesn't align with your target positions ({', '.join(t.title() for t in target_roles[:2])})")
    
    score += role_score
    
    # 1.2 SKILL OVERLAP (20 points) - With specific evidence from achievements
    skill_score = 0
    resume_skills = []
    
    # Common technical and business skills to check
    skill_library = [
        "python", "javascript", "java", "sql", "excel", "tableau", "power bi",
        "aws", "azure", "docker", "kubernetes", "react", "node", "angular",
        "machine learning", "data analysis", "project management", "agile",
        "salesforce", "sap", "oracle", "mongodb", "postgresql", "git",
        "financial modeling", "budgeting", "forecasting", "reporting",
        "leadership", "stakeholder management", "workday", "peoplesoft",
        "communication", "teamwork", "problem solving", "analytical",
        "c++", "rust", "golang", "typescript", "html", "css"
    ]
    
    # Check profile skills and find meaningful evidence
    for skill in profile_skills:
        skill_lower = skill.lower()
        if skill_lower in job_desc or skill_lower in job_title:
            matched_skills.append(skill)
            
            # Find meaningful evidence from achievements (not raw text)
            evidence = find_skill_evidence(skill, resume_text_raw, resume_achievements)
            if evidence and len(grounded_strengths) < 5:
                grounded_strengths.append({
                    "strength_title": f"{skill} Proficiency",
                    "evidence": evidence,
                    "relevance": f"Job requires {skill} - your experience directly addresses this"
                })
    
    # Check resume for additional skills from skill library
    if has_resume:
        for skill in skill_library:
            if skill in job_desc and skill in resume_text:
                if skill not in [s.lower() for s in matched_skills]:
                    resume_skills.append(skill.title())
                    
                    # Add grounded strength with meaningful evidence
                    evidence = find_skill_evidence(skill, resume_text_raw, resume_achievements)
                    if evidence and len(grounded_strengths) < 5:
                        grounded_strengths.append({
                            "strength_title": f"{skill.title()} Experience",
                            "evidence": evidence,
                            "relevance": f"Resume demonstrates hands-on {skill.title()} usage relevant to this role"
                        })
    
    all_skills = matched_skills + resume_skills
    
    if all_skills:
        # Weight: more skills = higher score, cap at 20
        skill_ratio = min(len(all_skills) / 5, 1.0)
        skill_score = int(skill_ratio * 20)
        
        if len(all_skills) >= 3:
            strengths.append(f"Strong skill match: {', '.join(all_skills[:4])}")
    else:
        skill_score = 3
        if profile_skills or has_resume:
            gaps.append(f"Limited skill overlap - consider highlighting transferable skills")
    
    score += skill_score
    
    # 1.3 EXPERIENCE SCOPE (20 points) - Seniority based on scope, not just years
    exp_score = 0
    seniority_gap = 0
    
    # Detect job seniority from title
    job_seniority_level = 2  # Default: mid
    job_seniority_name = "mid"
    
    if any(word in job_title for word in ["ceo", "cto", "cfo", "vp", "chief"]):
        job_seniority_level = 6
        job_seniority_name = "executive"
    elif any(word in job_title for word in ["director", "head of"]):
        job_seniority_level = 5
        job_seniority_name = "director"
    elif any(word in job_title for word in ["senior", "sr.", "lead", "principal", "staff"]):
        job_seniority_level = 3
        job_seniority_name = "senior"
    elif any(word in job_title for word in ["junior", "jr.", "entry", "associate", "graduate", "intern"]):
        job_seniority_level = 1
        job_seniority_name = "junior"
    elif any(word in job_title for word in ["manager"]):
        job_seniority_level = 4
        job_seniority_name = "manager"
    
    # Determine user seniority
    seniority_map = {"entry": 0, "junior": 1, "mid": 2, "senior": 3, "lead": 4, "manager": 4, "director": 5, "executive": 6}
    user_seniority_level = seniority_map.get(user_seniority, None)
    
    # Infer from years if not set
    if user_seniority_level is None:
        if user_years <= 2:
            user_seniority_level = 1
            user_seniority = "junior"
        elif user_years <= 5:
            user_seniority_level = 2
            user_seniority = "mid"
        elif user_years <= 8:
            user_seniority_level = 3
            user_seniority = "senior"
        else:
            user_seniority_level = 4
            user_seniority = "lead"
    
    seniority_gap = job_seniority_level - user_seniority_level
    
    # Scoring based on seniority alignment
    if seniority_gap == 0:
        exp_score = 20
        strengths.append(f"Experience aligns well: Your {user_seniority}-level background matches this {job_seniority_name} position")
    elif seniority_gap == 1:
        exp_score = 15
        risks.append(f"One level stretch: This {job_seniority_name} role is one level above your {user_seniority} position - achievable with strong application")
    elif seniority_gap == -1:
        exp_score = 18
        strengths.append(f"Solid fit: Your {user_seniority}-level experience exceeds this {job_seniority_name} position")
    elif seniority_gap >= 2:
        exp_score = 5
        risks.append(f"Significant stretch: This {job_seniority_name} role is {seniority_gap} levels above your current {user_seniority} level - high risk")
        auto_apply_blocked = True
        auto_apply_reason = "Seniority gap exceeds one level"
    elif seniority_gap <= -2:
        exp_score = 10
        risks.append(f"Overqualified: This {job_seniority_name} role may be below your {user_seniority}-level experience")
    
    # Resume evidence boost
    if has_resume and user_years > 0:
        leadership_keywords = ["led", "managed", "directed", "owned", "coordinated", "supervised"]
        if any(kw in resume_text for kw in leadership_keywords):
            exp_score = min(exp_score + 2, 20)
    
    score += exp_score

    
    # ============================================================================
    # CATEGORY 2: CONSTRAINTS & PRACTICALITY (25 points) - Can I apply?
    # ============================================================================
    
    # 2.1 LOCATION / REMOTE FIT (10 points)
    location_score = 0
    preferred_locations = [loc.lower() for loc in profile.get("preferred_locations", [])]
    
    if is_remote:
        location_score = 10
        strengths.append("Remote position offers location flexibility")
    elif preferred_locations and any(loc in job_location for loc in preferred_locations):
        location_score = 10
        strengths.append(f"Location matches your preferences")
    elif preferred_locations:
        location_score = 3
        gaps.append("Location may not match your preferences - consider if relocation is feasible")
    else:
        location_score = 7  # No preference set, give partial credit
    
    score += location_score
    
    # 2.2 INDUSTRY ALIGNMENT (5 points)
    industry_score = 0
    industries = [ind.lower() for ind in profile.get("industries", [])]
    open_to_any = profile.get("open_to_any_industry", False)
    
    if open_to_any:
        industry_score = 5
    elif industries:
        # Simplified industry check
        industry_matched = False
        for ind in industries:
            if ind in company_name.lower() or ind in job_desc:
                industry_score = 5
                industry_matched = True
                break
        
        if not industry_matched:
            industry_score = 2
            gaps.append("Industry alignment unclear - may require additional research on company")
    else:
        industry_score = 4  # No preference, neutral
    
    score += industry_score
    
    # 2.3 SALARY ALIGNMENT (5 points) - Don't penalize heavily if missing
    salary_score = 4  # Default: assume okay if not specified
    job_min_salary = job.get("job_min_salary")
    user_min_salary = profile.get("salary_min")
    
    if job_min_salary and user_min_salary:
        if job_min_salary >= user_min_salary:
            salary_score = 5
            strengths.append(f"Salary (${job_min_salary:,}+) meets your requirements")
        else:
            salary_score = 1
            risks.append("Salary may be below your minimum - negotiate or clarify compensation")
    
    score += salary_score
    
    # 2.4 WORK AUTHORIZATION / ELIGIBILITY (5 points) - CRITICAL
    auth_score = 5  # Default: assume eligible
    work_auth = profile.get("work_authorization", "")
    
    if work_auth == "require_sponsorship":
        blockers = ["no sponsorship", "must be authorized", "no visa", "pr only"]
        if any(blocker in job_desc.lower() for blocker in blockers):
            auth_score = 0
            auto_apply_blocked = True
            auto_apply_reason = "Work authorization requirement not met"
            risks.append("CRITICAL: Role does not offer sponsorship - not eligible to apply")
    
    score += auth_score
    
    # ============================================================================
    # CATEGORY 3: CONFIDENCE & RISK ADJUSTERS (15 points) - How risky is this?
    # ============================================================================
    
    # 3.1 RESUME EVIDENCE STRENGTH (5 points)
    resume_score = 0
    if has_resume:
        # Check for substantive content
        if len(resume_text) > 500:
            resume_score = 5
        elif len(resume_text) > 200:
            resume_score = 3
        else:
            resume_score = 1
            auto_apply_blocked = True
            auto_apply_reason = "Weak resume evidence"
    else:
        resume_score = 0
        gaps.append("Upload resume for stronger application and better match analysis")
        auto_apply_blocked = True
        auto_apply_reason = "No resume uploaded"
    
    score += resume_score
    
    # 3.2 ATS COMPATIBILITY (5 points)
    ats_score = 5  # Bonus for Greenhouse/Lever/Ashby
    source = job.get("source", "")
    if source in ["greenhouse", "lever", "ashby"]:
        ats_score = 5  # Full points - these are friendly ATS
    elif source == "aggregator":
        ats_score = 3  # Neutral for other sources
    
    score += ats_score
    
    # 3.3 SENIORITY STRETCH INDICATOR (5 points)
    stretch_score = 0
    if seniority_gap == 0:
        stretch_score = 5
    elif abs(seniority_gap) == 1:
        stretch_score = 3
    else:
        stretch_score = 1
    
    score += stretch_score
    
    # Contextual bonuses (capped at +5 total)
    bonus = 0
    if has_resume and company_name.lower() in resume_text:
        bonus += 2
        strengths.append(f"Previous exposure to {company_name} strengthens your application")
    
    score = min(score + bonus, 92)  # Cap at 92, never show above 92%
    
    # ============================================================================
    # DETERMINE MATCH LABEL, CONFIDENCE, RISK
    # ============================================================================
    
    if score >= 85:
        recommendation = "strong_match"
        match_label = "Strong Match"
    elif score >= 70:
        recommendation = "good_match"
        match_label = "Good Match"
    elif score > 65:
        recommendation = "review"
        match_label = "Review"
    else:
        # 65% or below is "Not Recommended"
        recommendation = "not_recommended"
        match_label = "Not Recommended"
    
    # Confidence level
    if has_resume and len(all_skills) >= 3 and role_matched:
        confidence = "high"
    elif has_resume or (len(all_skills) >= 2 and role_matched):
        confidence = "medium"
    else:
        confidence = "low"
    
    # Risk level
    if auto_apply_blocked or seniority_gap >= 2 or auth_score == 0:
        risk = "high"
        risk_explanation = "Significant barriers or misalignment detected"
    elif seniority_gap == 1 or len(all_skills) < 2:
        risk = "moderate"
        risk_explanation = "Some stretch or skill gaps present"
    else:
        risk = "low"
        risk_explanation = "Strong alignment across key factors"
    
    # ============================================================================
    # DECISION SUMMARY (REQUIRED)
    # ============================================================================
    
    if recommendation == "strong_match":
        decision_summary = f"Strong alignment with {company_name}'s needs. {risk_explanation}. Highly recommended to apply."
    elif recommendation == "good_match":
        decision_summary = f"Solid match with {company_name}. {risk_explanation}. Worth applying with tailored application."
    elif recommendation == "review":
        decision_summary = f"Potential fit at {company_name}. {risk_explanation}. Review carefully before applying."
    else:
        # not_recommended (65% or below)
        decision_summary = f"Limited alignment with requirements. {risk_explanation}. Not recommended - consider focusing on better-fit opportunities."
    
    # ============================================================================
    # OPTIONAL VALUE ADD (for matches ≥70%)
    # ============================================================================
    
    value_add = None
    if score >= 70:
        value_add = f"This role at {company_name} offers career leverage through {job_seniority_name}-level responsibilities and skill development in {', '.join(all_skills[:2]) if all_skills else 'key areas'}."
    
    # Match reasoning (user-facing explanation)
    if score >= 70:
        match_reasoning = f"{match_label}: Your background aligns well with this {job_title_display} position. {', '.join(strengths[:2]) if strengths else 'Core requirements match your profile'}."
    else:
        match_reasoning = f"{match_label}: {', '.join(risks[:2]) if risks else 'Significant gaps detected'}. {decision_summary}"
    
    # Enhance grounded strengths with meaningful achievements if not already populated
    if has_resume and len(grounded_strengths) < 5:
        # Track used categories to avoid duplicates
        used_categories = set(gs.get("strength_title", "") for gs in grounded_strengths)
        
        # Add achievement-based strengths that contain numbers or metrics
        for achievement in resume_achievements:
            if len(grounded_strengths) >= 5:
                break
            
            # Skip if already covered by skill-based strengths
            already_covered = any(
                achievement.lower() in gs.get("evidence", "").lower() 
                for gs in grounded_strengths
            )
            if already_covered:
                continue
            
            # Look for achievements with metrics (numbers, percentages, dollar amounts)
            if re.search(r'\d+%|\$[\d,]+|\d+\+?\s*(years?|months?|hours?|projects?|clients?|users?|teams?)', achievement, re.IGNORECASE):
                # Determine what kind of achievement this is - with unique titles
                ach_lower = achievement.lower()
                if any(kw in ach_lower for kw in ["led", "managed", "team", "cross-functional", "coordinated"]):
                    achievement_type = "Leadership & Collaboration"
                    relevance = "Demonstrates ability to lead teams and coordinate efforts"
                elif any(kw in ach_lower for kw in ["saved", "reduced", "cost", "budget"]):
                    achievement_type = "Cost Optimization"
                    relevance = "Track record of reducing costs and improving efficiency"
                elif any(kw in ach_lower for kw in ["improved", "increased", "grew", "generated", "revenue"]):
                    achievement_type = "Business Impact"
                    relevance = "History of driving measurable business improvements"
                elif any(kw in ach_lower for kw in ["built", "developed", "created", "designed"]):
                    achievement_type = "Technical Building"
                    relevance = "Hands-on experience building and shipping products"
                elif any(kw in ach_lower for kw in ["implemented", "deployed", "launched", "automated"]):
                    achievement_type = "System Implementation"
                    relevance = "Proven ability to implement and deploy systems"
                elif any(kw in ach_lower for kw in ["testing", "coverage", "quality", "ci/cd", "pipeline"]):
                    achievement_type = "Quality & DevOps"
                    relevance = "Experience with quality assurance and delivery pipelines"
                else:
                    achievement_type = "Measurable Achievement"
                    relevance = "Demonstrates ability to deliver quantifiable results"
                
                # Avoid duplicate category titles
                if achievement_type in used_categories:
                    # Add a suffix to differentiate
                    count = sum(1 for c in used_categories if achievement_type in c)
                    achievement_type = f"{achievement_type} ({count + 1})"
                
                used_categories.add(achievement_type)
                grounded_strengths.append({
                    "strength_title": achievement_type,
                    "evidence": achievement,
                    "relevance": relevance
                })
        
        # Add experience summary if we still have room
        if work_experiences and len(grounded_strengths) < 5:
            exp = work_experiences[0]
            if exp.get("company") and exp.get("title"):
                grounded_strengths.append({
                    "strength_title": "Relevant Work Experience",
                    "evidence": f"{exp['title']} at {exp['company']}",
                    "relevance": f"Background in similar role supports transition to {job_title_display}"
                })
    
    return {
        "score": score,
        "recommendation": recommendation,
        "match_label": match_label,
        "confidence": confidence,
        "risk": risk,
        "decision_summary": decision_summary,
        "strengths": strengths[:3],  # Max 3 (legacy format)
        "grounded_strengths": grounded_strengths[:5],  # Resume-grounded strengths with evidence
        "gaps": (risks + gaps)[:2],  # Max 2, prioritize risks
        "match_reasoning": match_reasoning,
        "value_add": value_add,
        "skip_reason": None if score >= 55 else "Below recommended match threshold",
        "auto_apply_blocked": auto_apply_blocked,
        "auto_apply_reason": auto_apply_reason,
        "matched_skills": all_skills[:5],  # Expose matched skills
        "job_seniority": job_seniority_name,
        "user_seniority": user_seniority or "not specified",
    }


def calculate_match_score(job: Dict, profile: Optional[Dict]) -> int:
    """Legacy function - returns just the score for backward compatibility."""
    result = evaluate_job_match(job, profile)
    return result["score"]

# ========================
# AI ROUTES
# ========================

