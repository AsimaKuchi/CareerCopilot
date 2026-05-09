"""
routes/resume_routes.py - Resume upload, parse, extract and download.

Endpoints (under /api):
  POST /profile/resume                  -- Upload and parse resume (PDF/DOCX/TXT)
  POST /profile/resume/extract-fields   -- Extract structured fields from resume text
  POST /profile/resume/reparse          -- Re-run parsing on stored resume
  GET  /profile/resume/download/original -- Download originally-uploaded resume

Helper functions:
  extract_text_from_docx(content)
  extract_text_from_pdf(content)

Refactored from monolithic server.py (Feb 2026).
"""
from datetime import datetime, timezone
from typing import Optional
import io
import base64
import json
import re
import uuid

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import Response
import httpx

from docx import Document
from PyPDF2 import PdfReader

from core import db, logger, EMERGENT_LLM_KEY, get_current_user
from profile_schema import migrate_profile_to_v2
from encryption import encrypt_field, decrypt_field, decrypt_sensitive_data

router = APIRouter()


def extract_text_from_docx(content: bytes) -> str:
    """Extract text from DOCX file while preserving structure and formatting."""
    try:
        doc = Document(io.BytesIO(content))
        lines = []
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                # Check for bullet points or list items
                if para.style and para.style.name:
                    style = para.style.name.lower()
                    if 'heading' in style or 'title' in style:
                        # Add spacing before headings
                        if lines:
                            lines.append('')
                        lines.append(text.upper())
                        lines.append('')
                    elif 'list' in style or 'bullet' in style:
                        lines.append(f"• {text}")
                    else:
                        lines.append(text)
                else:
                    # Check if paragraph has bullet formatting
                    if para._element.pPr is not None:
                        numPr = para._element.pPr.numPr
                        if numPr is not None:
                            lines.append(f"• {text}")
                        else:
                            lines.append(text)
                    else:
                        lines.append(text)
        
        # Also extract text from tables
        for table in doc.tables:
            for row in table.rows:
                row_text = ' | '.join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    lines.append(row_text)
        
        return '\n'.join(lines)
    except Exception as e:
        logger.error(f"Error extracting DOCX text: {str(e)}")
        return ""

def extract_text_from_pdf(content: bytes) -> str:
    """Extract text from PDF file."""
    try:
        reader = PdfReader(io.BytesIO(content))
        text_parts = []
        
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        return '\n\n'.join(text_parts)
    except Exception as e:
        logger.error(f"Error extracting PDF text: {str(e)}")
        return ""

# ========================
# GREENHOUSE JOB SCRAPER
# ========================

@router.post("/profile/resume")
async def upload_resume(request: Request, file: UploadFile = File(...)):
    """Upload and parse resume from DOCX, PDF, or TXT files."""
    try:
        user = await get_current_user(request)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Auth error in resume upload: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")
    
    try:
        content = await file.read()
        
        if not content:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        filename = file.filename.lower() if file.filename else ""
        resume_text = ""
        resume_format = "text"
        
        # Parse based on file type
        if filename.endswith('.docx'):
            resume_text = extract_text_from_docx(content)
            resume_format = "docx"
            if not resume_text:
                raise HTTPException(status_code=400, detail="Could not extract text from DOCX file")
        elif filename.endswith('.pdf'):
            resume_text = extract_text_from_pdf(content)
            resume_format = "pdf"
            if not resume_text:
                raise HTTPException(status_code=400, detail="Could not extract text from PDF file")
        elif filename.endswith('.doc'):
            # .doc files are not directly supported, store as base64
            resume_text = "[Legacy .doc format - please convert to .docx for full text extraction]"
            resume_format = "doc"
        else:
            # Try to decode as text
            try:
                resume_text = content.decode('utf-8')
                resume_format = "text"
            except UnicodeDecodeError:
                resume_text = base64.b64encode(content).decode('utf-8')
                resume_format = "binary"
        
        # Store the raw content as base64 for potential future use
        raw_content_b64 = base64.b64encode(content).decode('utf-8')
        
        await db.user_profiles.update_one(
            {"user_id": user.user_id},
            {"$set": {
                "resume_text": encrypt_field(resume_text),
                "resume_raw": encrypt_field(raw_content_b64),
                "resume_filename": file.filename,
                "resume_format": resume_format,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        
        logger.info(f"Resume uploaded for user {user.user_id}: {file.filename} (format: {resume_format}, encrypted: yes)")
        return {
            "message": "Resume uploaded and encrypted successfully", 
            "filename": file.filename,
            "format": resume_format,
            "text_extracted": len(resume_text) > 0,
            "encrypted": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload resume: {str(e)}")


@router.post("/profile/resume/extract-fields")
async def extract_fields_from_resume(request: Request):
    """Extract profile fields (email, phone, skills, education, location, job titles) from uploaded resume text.
    Returns only fields that are currently empty in the user's profile."""
    user = await get_current_user(request)

    profile = await db.user_profiles.find_one({"user_id": user.user_id}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=400, detail="Profile not found")

    profile = decrypt_sensitive_data(profile)
    resume_text = profile.get("resume_text", "")
    if not resume_text or len(resume_text) < 50:
        raise HTTPException(status_code=400, detail="No resume text available")

    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import json as json_mod

    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"extract_{user.user_id}_{uuid.uuid4().hex[:6]}",
        system_message="""Extract structured profile fields from a resume. Return ONLY valid JSON, no markdown.
{
  "email": "string or null",
  "phone": "string in E.164-ish format or null",
  "skills": ["skill1", "skill2"],
  "highest_education": "one of: high_school, associate, bachelors, masters, phd, bootcamp, certification, or null",
  "education_details": "e.g. Bachelor of Commerce, University of Toronto",
  "job_titles": ["most recent title", "second most recent"],
  "city": "string or null",
  "state_province": "string or null",
  "country": "string or null",
  "experience_years": number or null,
  "first_name": "string or null",
  "last_name": "string or null"
}
Rules:
- For highest_education pick the HIGHEST level found.
- For skills, list up to 20 distinct professional skills.
- For job_titles, list the 1-3 most recent titles.
- Phone: include country code if visible, e.g. +14165551234
- Return null for anything you can't confidently extract."""
    ).with_model("openai", "gpt-4o-mini")

    try:
        response = await chat.send_message(
            UserMessage(text=f"Extract profile fields from this resume:\n\n{resume_text[:3000]}")
        )
        clean = re.sub(r'^```json\s*', '', response.strip())
        clean = re.sub(r'\s*```$', '', clean).strip()
        extracted = json_mod.loads(clean)
    except Exception as e:
        logger.error(f"Resume field extraction failed: {e}")
        raise HTTPException(status_code=500, detail="Could not extract fields from resume")

    # Determine which profile fields are currently empty
    existing_skills = profile.get("skills") or []
    existing_skill_names = {(s.get("name") if isinstance(s, dict) else s).lower() for s in existing_skills}

    suggestions = {}

    if not profile.get("phone_number") and extracted.get("phone"):
        suggestions["phone_number"] = extracted["phone"]

    if not profile.get("highest_education") and extracted.get("highest_education"):
        suggestions["highest_education"] = extracted["highest_education"]
        if extracted.get("education_details"):
            suggestions["education_details"] = extracted["education_details"]

    if not existing_skills and extracted.get("skills"):
        suggestions["skills"] = extracted["skills"][:20]
    elif extracted.get("skills"):
        new_skills = [s for s in extracted["skills"] if s.lower() not in existing_skill_names]
        if new_skills:
            suggestions["new_skills"] = new_skills[:15]

    if not profile.get("job_titles") and extracted.get("job_titles"):
        suggestions["job_titles"] = extracted["job_titles"]

    if not profile.get("address_city") and extracted.get("city"):
        suggestions["address_city"] = extracted["city"]
    if not profile.get("address_state") and extracted.get("state_province"):
        suggestions["address_state"] = extracted["state_province"]
    if not profile.get("address_country") and extracted.get("country"):
        suggestions["address_country"] = extracted["country"]

    if not profile.get("experience_years") and extracted.get("experience_years"):
        suggestions["experience_years"] = extracted["experience_years"]

    if not profile.get("first_name") and extracted.get("first_name"):
        suggestions["first_name"] = extracted["first_name"]
    if not profile.get("last_name") and extracted.get("last_name"):
        suggestions["last_name"] = extracted["last_name"]

    return {
        "suggestions": suggestions,
        "has_suggestions": len(suggestions) > 0,
    }


@router.post("/profile/resume/reparse")
async def reparse_resume(request: Request):
    """Re-extract text from stored resume raw content."""
    user = await get_current_user(request)
    
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    
    if not profile:
        raise HTTPException(status_code=400, detail="No profile found")
    
    # Check for raw content in resume_raw or base64 in resume_text
    raw_content = None
    
    if profile.get("resume_raw"):
        # Normal case: raw content stored separately
        try:
            raw_content = base64.b64decode(profile["resume_raw"])
        except Exception as e:
            logger.error(f"Failed to decode resume_raw: {e}")
    
    if not raw_content and profile.get("resume_text"):
        # Check if resume_text contains base64 data (starts with PK signature for DOCX/ZIP)
        resume_text = profile.get("resume_text", "")
        if resume_text.startswith("UEsDB"):  # Base64 of "PK" (ZIP/DOCX signature)
            try:
                raw_content = base64.b64decode(resume_text)
                logger.info("Decoded base64 from resume_text field")
            except Exception as e:
                logger.error(f"Failed to decode resume_text as base64: {e}")
    
    if not raw_content:
        raise HTTPException(status_code=400, detail="No resume raw content found to reparse")
    
    try:
        filename = profile.get("resume_filename", "").lower()
        resume_text = ""
        resume_format = ""
        
        # Try to extract based on filename extension
        if filename.endswith('.docx'):
            resume_text = extract_text_from_docx(raw_content)
            resume_format = "docx"
        elif filename.endswith('.pdf'):
            resume_text = extract_text_from_pdf(raw_content)
            resume_format = "pdf"
        else:
            # Try DOCX first (most common), then PDF, then text
            resume_text = extract_text_from_docx(raw_content)
            if resume_text:
                resume_format = "docx"
            else:
                resume_text = extract_text_from_pdf(raw_content)
                if resume_text:
                    resume_format = "pdf"
                else:
                    try:
                        resume_text = raw_content.decode('utf-8')
                        resume_format = "text"
                    except UnicodeDecodeError:
                        pass
        
        if not resume_text:
            raise HTTPException(status_code=400, detail="Could not extract text from resume. Please re-upload.")
        
        # Update the profile with extracted text and store raw content properly
        raw_b64 = base64.b64encode(raw_content).decode('utf-8')
        
        await db.user_profiles.update_one(
            {"user_id": user.user_id},
            {"$set": {
                "resume_text": resume_text,
                "resume_raw": raw_b64,
                "resume_format": resume_format,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        logger.info(f"Resume reparsed for user {user.user_id}: {len(resume_text)} chars extracted")
        return {
            "message": "Resume text re-extracted successfully",
            "text_length": len(resume_text),
            "format": resume_format
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume reparse error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reparse resume: {str(e)}")

@router.get("/profile/resume/download/original")
async def download_original_resume(request: Request):
    """
    Download the user's original resume file (preserves original format and formatting).
    Returns the file in its original format (PDF, DOCX, etc.)
    """
    user = await get_current_user(request)
    
    profile = await db.user_profiles.find_one(
        {"user_id": user.user_id},
        {"_id": 0, "resume_raw": 1, "resume_filename": 1, "resume_format": 1}
    )
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    resume_raw = profile.get("resume_raw")
    if not resume_raw:
        raise HTTPException(status_code=404, detail="No original resume file stored")
    
    # Decrypt if encrypted
    if isinstance(resume_raw, str) and resume_raw.startswith("gAAAAA"):
        resume_raw = decrypt_field(resume_raw)
    
    try:
        # Decode base64 to bytes
        file_content = base64.b64decode(resume_raw)
    except Exception as e:
        logger.error(f"Failed to decode resume_raw: {e}")
        raise HTTPException(status_code=500, detail="Failed to decode resume file")
    
    # Determine content type
    resume_format = profile.get("resume_format", "").lower()
    filename = profile.get("resume_filename", "resume")
    
    if resume_format == "pdf" or filename.endswith(".pdf"):
        content_type = "application/pdf"
    elif resume_format == "docx" or filename.endswith(".docx"):
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif resume_format == "doc" or filename.endswith(".doc"):
        content_type = "application/msword"
    else:
        content_type = "application/octet-stream"
    
    from fastapi.responses import Response
    return Response(
        content=file_content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

# ========================
# JOB SEARCH ROUTES
# ========================

