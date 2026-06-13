"""
job_url_match.py - Canonical job-URL matching.

Many ATSes expose the same job at multiple URLs:
    https://careers.airbnb.com/positions/7434393?gh_jid=7434393
    https://job-boards.greenhouse.io/airbnb/jobs/7434393
    https://stripe.com/jobs/search?gh_jid=7230921 -> job-boards.greenhouse.io/stripe/jobs/7230921

This module reduces any ATS URL to a stable canonical key like
``greenhouse:7434393`` or ``lever:airbnb/abc-123-uuid`` so the extension
autofill endpoint can reliably match the user-visited URL to a saved
application even when the user lands on a company-branded page instead of
the ATS-hosted page.

Used by:
  - routes/application_routes.py   (computes & stores ``apply_link_key`` on POST /applications)
  - routes/extension_routes.py     (computes key from incoming job_url and looks up matching application)
"""
from typing import Optional
from urllib.parse import urlparse, parse_qs
import re


# ----- Per-ATS canonicalizers ---------------------------------------------
def _greenhouse_key(url_lower: str, parsed) -> Optional[str]:
    """Greenhouse jobs share a numeric id across hosted (boards.greenhouse.io,
    job-boards.greenhouse.io) and company-branded pages (?gh_jid=...)."""
    # 1. ?gh_jid=12345 anywhere
    qs = parse_qs(parsed.query)
    if "gh_jid" in qs and qs["gh_jid"]:
        gid = qs["gh_jid"][0].strip()
        if gid.isdigit():
            return f"greenhouse:{gid}"

    # 2. /jobs/{id} on greenhouse.io subdomains
    m = re.search(r"greenhouse\.io/[^/]+/jobs/(\d+)", url_lower)
    if m:
        return f"greenhouse:{m.group(1)}"

    # 3. embed/job_app?token=...
    if "greenhouse.io/embed/job_app" in url_lower:
        token = qs.get("token", [""])[0]
        if token:
            return f"greenhouse:embed:{token}"

    # 4. Known company-branded greenhouse pages by URL pattern
    # careers.airbnb.com/positions/{id}
    if parsed.netloc.endswith("careers.airbnb.com"):
        m = re.search(r"/positions/(\d+)", parsed.path)
        if m:
            return f"greenhouse:{m.group(1)}"
    # jobs.dropbox.com/listing/{id}
    if parsed.netloc.endswith("jobs.dropbox.com"):
        m = re.search(r"/listing/(\d+)", parsed.path)
        if m:
            return f"greenhouse:{m.group(1)}"
    return None


def _lever_key(parsed) -> Optional[str]:
    """jobs.lever.co/{company}/{uuid}"""
    if "lever.co" not in parsed.netloc:
        return None
    m = re.match(r"^/([^/]+)/([a-f0-9-]{8,})", parsed.path)
    if m:
        return f"lever:{m.group(1)}/{m.group(2)}"
    return None


def _ashby_key(parsed) -> Optional[str]:
    """jobs.ashbyhq.com/{company}/{uuid}"""
    if "ashbyhq.com" not in parsed.netloc:
        return None
    m = re.match(r"^/([^/]+)/([a-f0-9-]{8,})", parsed.path)
    if m:
        return f"ashby:{m.group(1)}/{m.group(2)}"
    return None


def _linkedin_key(parsed) -> Optional[str]:
    """linkedin.com/jobs/view/{slug}-{id} or /jobs/view/{id}"""
    if "linkedin.com" not in parsed.netloc:
        return None
    # Match trailing numeric id of >= 8 digits
    m = re.search(r"/jobs/view/(?:.*?-)?(\d{8,})", parsed.path)
    if m:
        return f"linkedin:{m.group(1)}"
    return None


def _smartrecruiters_key(parsed) -> Optional[str]:
    """jobs.smartrecruiters.com/{company}/{numeric-id}-{slug}"""
    if "smartrecruiters.com" not in parsed.netloc:
        return None
    m = re.search(r"/([^/]+)/(\d{8,})", parsed.path)
    if m:
        return f"smartrecruiters:{m.group(2)}"
    return None


def _workday_key(parsed) -> Optional[str]:
    """*.myworkdayjobs.com/.../job/.../R-12345"""
    if "myworkdayjobs.com" not in parsed.netloc:
        return None
    m = re.search(r"/(R-?\d+)", parsed.path)
    if m:
        return f"workday:{parsed.netloc.split('.')[0]}:{m.group(1)}"
    return None


def _talent_key(parsed) -> Optional[str]:
    """ca.talent.com/view?id=abc123 and similar aggregators."""
    if "talent.com" not in parsed.netloc:
        return None
    qs = parse_qs(parsed.query)
    if "id" in qs and qs["id"]:
        return f"talent:{qs['id'][0]}"
    return None


# ----- Public API ----------------------------------------------------------
def canonical_job_key(url: Optional[str]) -> Optional[str]:
    """Return a stable canonical key for a job-posting URL.

    Returns None if the URL doesn't match a known ATS pattern (caller can
    then fall back to substring matching against the raw URL).
    """
    if not url or not isinstance(url, str):
        return None
    try:
        parsed = urlparse(url.strip())
    except Exception:
        return None
    if not parsed.netloc:
        return None
    url_lower = url.lower()

    for fn, arg in [
        (_greenhouse_key, (url_lower, parsed)),
        (_lever_key, (parsed,)),
        (_ashby_key, (parsed,)),
        (_smartrecruiters_key, (parsed,)),
        (_workday_key, (parsed,)),
        (_linkedin_key, (parsed,)),
        (_talent_key, (parsed,)),
    ]:
        try:
            key = fn(*arg)
            if key:
                return key
        except Exception:
            continue
    return None


def normalize_url_for_match(url: Optional[str]) -> Optional[str]:
    """Strip query, fragment and trailing slash so two visibly-identical URLs
    compare equal even when one has tracking params. Used as a fallback when
    canonical_job_key returns None."""
    if not url:
        return None
    try:
        parsed = urlparse(url.strip())
    except Exception:
        return None
    if not parsed.netloc:
        return None
    path = parsed.path.rstrip("/")
    return f"{parsed.scheme}://{parsed.netloc}{path}".lower()
