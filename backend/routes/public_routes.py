"""
routes/public_routes.py - Public Jobs API + support form (no auth required).

Mounted under /api/public except where the original prefix was overridden.
Endpoints:
  GET  /public/health             -- Health check
  POST /public/support            -- Submit a support request
  GET  /public/jobs               -- Browse cached jobs
  GET  /public/jobs/{job_id}      -- Single job detail
  POST /public/jobs/ingest        -- Trigger background ingestion
  GET  /public/sources            -- Source breakdown
  GET  /public/companies          -- Companies list

Helper:
  ingest_all_jobs() -- shared with the ingest scheduler

Refactored from monolithic server.py (Feb 2026).
"""
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
import asyncio
import uuid

from fastapi import APIRouter, HTTPException, Request
import httpx
import resend

from core import db, logger, SENDER_EMAIL, SUPPORT_EMAIL
from models import SupportRequest

# Imported lazily inside handlers to avoid circular imports:
#   - search_greenhouse_jobs, fetch_lever_company_jobs etc. (job_routes helpers)

router = APIRouter(prefix="/public", tags=["Public Jobs API"])


# ========================
# PUBLIC JOBS API (Phase 1)
# For Lovable Frontend Integration
# ========================

@router.get("/health")
async def public_health():
    """Health check endpoint."""
    job_count = await db.stored_jobs.count_documents({})
    
    # Get next scheduled run time (lazy import to avoid circular dep with server.py)
    next_run = None
    try:
        from server import scheduler as _scheduler
        job = _scheduler.get_job("job_ingestion")
        if job and job.next_run_time:
            next_run = job.next_run_time.isoformat()
    except Exception:
        pass
    
    return {
        "status": "healthy",
        "service": "MyCareerCoPilot API",
        "version": "1.0.0",
        "jobs_in_database": job_count,
        "auto_refresh": {
            "enabled": True,
            "interval": "every 2 hours",
            "next_refresh": next_run
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.post("/support")
async def submit_support_request(request: SupportRequest):
    """Submit a support request - sends email to support team."""
    try:
        # Create HTML email content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); padding: 20px; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">New Support Request</h1>
            </div>
            <div style="background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 10px 10px;">
                <h2 style="color: #374151; margin-top: 0;">Contact Information</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; color: #6b7280; width: 120px;"><strong>Name:</strong></td>
                        <td style="padding: 8px 0; color: #111827;">{request.first_name} {request.last_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #6b7280;"><strong>Email:</strong></td>
                        <td style="padding: 8px 0; color: #111827;"><a href="mailto:{request.email}" style="color: #6366f1;">{request.email}</a></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #6b7280;"><strong>Reason:</strong></td>
                        <td style="padding: 8px 0; color: #111827;">{request.reason}</td>
                    </tr>
                </table>
                
                <h2 style="color: #374151; margin-top: 24px;">Description</h2>
                <div style="background: white; padding: 16px; border-radius: 8px; border: 1px solid #e5e7eb;">
                    <p style="color: #374151; margin: 0; white-space: pre-wrap; line-height: 1.6;">{request.description}</p>
                </div>
                
                <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
                    <p style="color: #9ca3af; font-size: 12px; margin: 0;">
                        Sent from MyCareerCoPilot Support Form • {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send email via Resend
        params = {
            "from": SENDER_EMAIL,
            "to": [SUPPORT_EMAIL],
            "subject": f"[Support] {request.reason} - {request.first_name} {request.last_name}",
            "html": html_content,
            "reply_to": request.email
        }
        
        # Run sync SDK in thread to keep FastAPI non-blocking
        email_result = await asyncio.to_thread(resend.Emails.send, params)
        
        # Store in database for tracking
        support_doc = {
            "support_id": str(uuid.uuid4()),
            "first_name": request.first_name,
            "last_name": request.last_name,
            "email": request.email,
            "reason": request.reason,
            "description": request.description,
            "email_id": email_result.get("id") if email_result else None,
            "status": "sent",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.support_requests.insert_one(support_doc)
        
        logger.info(f"Support request submitted by {request.email}: {request.reason}")
        
        return {
            "success": True,
            "message": "Your support request has been submitted. We'll get back to you soon!"
        }
        
    except Exception as e:
        logger.error(f"Failed to submit support request: {str(e)}")
        
        # Still store it even if email fails
        support_doc = {
            "support_id": str(uuid.uuid4()),
            "first_name": request.first_name,
            "last_name": request.last_name,
            "email": request.email,
            "reason": request.reason,
            "description": request.description,
            "email_id": None,
            "status": "email_failed",
            "error": str(e),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.support_requests.insert_one(support_doc)
        
        return {
            "success": True,
            "message": "Your request has been received. We'll get back to you soon!"
        }

@router.get("/jobs")
async def get_jobs(
    page: int = 1,
    limit: int = 20,
    query: Optional[str] = None,
    location: Optional[str] = None,
    company: Optional[str] = None,
    source: Optional[str] = None,  # greenhouse, lever, jsearch
    remote_only: bool = False,
    posted_after: Optional[str] = None,  # ISO date string
    sort_by: str = "posted_at_dt",  # posted_at_dt, company, title
    sort_order: str = "desc"  # asc, desc
):
    """
    Get paginated list of jobs with filtering.
    Returns UI-ready JSON.
    """
    # Build filter
    filter_query = {}
    
    if query:
        # Search in title and description
        filter_query["$or"] = [
            {"title": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}},
            {"company": {"$regex": query, "$options": "i"}}
        ]
    
    if location:
        filter_query["location"] = {"$regex": location, "$options": "i"}
    
    if company:
        filter_query["company"] = {"$regex": company, "$options": "i"}
    
    if source:
        filter_query["source"] = source
    
    if remote_only:
        filter_query["is_remote"] = True
    
    if posted_after:
        try:
            posted_date = datetime.fromisoformat(posted_after.replace('Z', '+00:00'))
            filter_query["posted_at"] = {"$gte": posted_date}
        except:
            pass
    
    # Pagination
    skip = (page - 1) * limit
    limit = min(limit, 100)  # Max 100 per page
    
    # Sort
    sort_direction = -1 if sort_order == "desc" else 1
    sort_field = sort_by if sort_by in ["posted_at_dt", "posted_at", "company", "title"] else "posted_at_dt"
    
    # Get total count
    total = await db.stored_jobs.count_documents(filter_query)
    
    # Get jobs
    cursor = db.stored_jobs.find(filter_query, {"_id": 0}).sort(sort_field, sort_direction).skip(skip).limit(limit)
    jobs = await cursor.to_list(length=limit)
    
    # Format for UI
    formatted_jobs = []
    for job in jobs:
        # Handle posted_at - prefer normalized datetime
        posted_at_dt = job.get("posted_at_dt")
        posted_at = job.get("posted_at")
        if posted_at_dt:
            if hasattr(posted_at_dt, 'isoformat'):
                posted_at = posted_at_dt.isoformat()
        elif posted_at:
            if hasattr(posted_at, 'isoformat'):
                posted_at = posted_at.isoformat()
        
        # Ensure description is clean plain text
        raw_desc = job.get("description", "")
        if raw_desc and ("<p>" in raw_desc or "<div>" in raw_desc or "<strong>" in raw_desc):
            from html import unescape
            raw_desc = unescape(raw_desc)
            soup = BeautifulSoup(raw_desc, 'html.parser')
            raw_desc = soup.get_text(separator='\n', strip=True)
        
        formatted_jobs.append({
            "id": job.get("job_id"),
            "title": job.get("title"),
            "company": job.get("company"),
            "location": job.get("location"),
            "description": raw_desc,
            "description_preview": (raw_desc[:300] + "...") if len(raw_desc) > 300 else raw_desc,
            "apply_url": job.get("apply_link"),
            "source": job.get("source"),
            "is_remote": job.get("is_remote", False),
            "posted_at": posted_at,
            "department": job.get("department"),
            "employment_type": job.get("employment_type")
        })
    
    return {
        "jobs": formatted_jobs,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit,
            "has_next": skip + limit < total,
            "has_prev": page > 1
        },
        "filters_applied": {
            "query": query,
            "location": location,
            "company": company,
            "source": source,
            "remote_only": remote_only
        }
    }

@router.get("/jobs/{job_id}")
async def get_job_by_id(job_id: str):
    """
    Get full job details by ID.
    Returns complete job data including full description.
    """
    job = await db.stored_jobs.find_one({"job_id": job_id}, {"_id": 0})
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Helper to safely format dates
    def format_date(d):
        if d is None:
            return None
        if hasattr(d, 'isoformat'):
            return d.isoformat()
        return str(d)
    
    return {
        "id": job.get("job_id"),
        "title": job.get("title"),
        "company": job.get("company"),
        "location": job.get("location"),
        "description": job.get("description"),
        "apply_url": job.get("apply_link"),
        "source": job.get("source"),
        "source_url": job.get("source_url"),
        "is_remote": job.get("is_remote", False),
        "posted_at": format_date(job.get("posted_at")),
        "department": job.get("department"),
        "employment_type": job.get("employment_type"),
        "salary_min": job.get("salary_min"),
        "salary_max": job.get("salary_max"),
        "requirements": job.get("requirements", []),
        "benefits": job.get("benefits", []),
        "metadata": {
            "ingested_at": format_date(job.get("ingested_at")),
            "last_updated": format_date(job.get("last_updated"))
        }
    }

@router.post("/jobs/ingest")
async def trigger_job_ingestion(background: bool = True):
    """
    Trigger job ingestion from all sources.
    This fetches jobs from Greenhouse/Lever and stores them in the database.
    """
    if background:
        # Run in background
        asyncio.create_task(ingest_all_jobs())
        return {"status": "started", "message": "Job ingestion started in background"}
    else:
        # Run synchronously (may take a while)
        result = await ingest_all_jobs()
        return result

async def ingest_all_jobs():
    """Fetch jobs from all sources and store in database."""
    logger.info("Starting job ingestion...")
    total_ingested = 0
    errors = []
    
    # Cleanup expired jobs first
    await cleanup_expired_jobs(days_old=30)
    
    # Ingest from Greenhouse
    for company in GREENHOUSE_COMPANIES:
        try:
            jobs = await fetch_greenhouse_company_jobs(company)
            for job in jobs:
                job["ingested_at"] = datetime.now(timezone.utc)
                job["last_updated"] = datetime.now(timezone.utc)
                job["is_remote"] = "remote" in job.get("location", "").lower()
                job["posted_at_dt"] = normalize_posted_date(job.get("posted_at"))
                
                await db.stored_jobs.update_one(
                    {"job_id": job["job_id"]},
                    {"$set": job},
                    upsert=True
                )
                total_ingested += 1
        except Exception as e:
            errors.append(f"Greenhouse/{company}: {str(e)}")
    
    # Ingest from Lever
    for company in LEVER_COMPANIES:
        try:
            jobs = await fetch_lever_company_jobs(company)
            for job in jobs:
                job["ingested_at"] = datetime.now(timezone.utc)
                job["last_updated"] = datetime.now(timezone.utc)
                job["is_remote"] = "remote" in job.get("location", "").lower()
                job["posted_at_dt"] = normalize_posted_date(job.get("posted_at"))
                
                await db.stored_jobs.update_one(
                    {"job_id": job["job_id"]},
                    {"$set": job},
                    upsert=True
                )
                total_ingested += 1
        except Exception as e:
            errors.append(f"Lever/{company}: {str(e)}")
    
    # Ingest from Amazon (custom API)
    try:
        amazon_jobs = await fetch_amazon_jobs(max_pages=5)
        for job in amazon_jobs:
            job["ingested_at"] = datetime.now(timezone.utc)
            job["last_updated"] = datetime.now(timezone.utc)
            job["is_remote"] = "remote" in job.get("location", "").lower()
            job["posted_at_dt"] = normalize_posted_date(job.get("posted_at"))
            
            await db.stored_jobs.update_one(
                {"job_id": job["job_id"]},
                {"$set": job},
                upsert=True
            )
            total_ingested += 1
    except Exception as e:
        errors.append(f"Amazon: {str(e)}")
    
    # Ingest from Microsoft & Apple via JSearch
    for company in ["Microsoft", "Apple"]:
        try:
            company_jobs = await fetch_company_jobs_via_jsearch(company, max_results=50)
            for job in company_jobs:
                job["ingested_at"] = datetime.now(timezone.utc)
                job["last_updated"] = datetime.now(timezone.utc)
                job["is_remote"] = "remote" in job.get("location", "").lower()
                job["posted_at_dt"] = normalize_posted_date(job.get("posted_at"))
                
                await db.stored_jobs.update_one(
                    {"job_id": job["job_id"]},
                    {"$set": job},
                    upsert=True
                )
                total_ingested += 1
        except Exception as e:
            errors.append(f"JSearch/{company}: {str(e)}")
    
    logger.info(f"Job ingestion complete: {total_ingested} jobs")
    
    return {
        "status": "complete",
        "jobs_ingested": total_ingested,
        "errors": errors if errors else None,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/sources")
async def get_job_sources():
    """Get list of available job sources and their job counts."""
    pipeline = [
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    results = await db.stored_jobs.aggregate(pipeline).to_list(length=100)
    
    sources = [{"source": r["_id"], "job_count": r["count"]} for r in results]
    
    return {
        "sources": sources,
        "total_jobs": sum(s["job_count"] for s in sources)
    }

@router.get("/companies")
async def get_companies(limit: int = 50):
    """Get list of companies with job counts."""
    pipeline = [
        {"$group": {"_id": "$company", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]
    
    results = await db.stored_jobs.aggregate(pipeline).to_list(length=limit)
    
    return {
        "companies": [{"name": r["_id"], "job_count": r["count"]} for r in results]
    }

# ========================
# AUTH HELPERS
# ========================

