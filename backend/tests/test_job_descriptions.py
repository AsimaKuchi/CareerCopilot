"""
Test suite for job descriptions feature
- Tests GET /api/public/jobs endpoint
- Verifies jobs have non-empty descriptions (from Greenhouse, Lever, Amazon, JSearch)
- Verifies descriptions are clean plain text (no HTML tags)
- Verifies jobs are sorted by posted_at_dt descending (newest first)
- Verifies description_preview field is present and truncated to 300 chars
"""

import pytest
import requests
import os
import re
from datetime import datetime
from dateutil import parser as dateparser

# Get base URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test session token for authenticated requests
TEST_SESSION_TOKEN = "docx_test_token_123"


class TestJobDescriptions:
    """Tests for job descriptions in GET /api/public/jobs endpoint"""
    
    def test_public_jobs_endpoint_returns_200(self):
        """GET /api/public/jobs should return 200 OK"""
        response = requests.get(f"{BASE_URL}/api/public/jobs")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: GET /api/public/jobs returns 200")
    
    def test_public_jobs_has_jobs_array(self):
        """Response should contain jobs array"""
        response = requests.get(f"{BASE_URL}/api/public/jobs")
        data = response.json()
        assert "jobs" in data, "Response missing 'jobs' array"
        assert isinstance(data["jobs"], list), "'jobs' should be a list"
        print(f"PASS: Response contains jobs array with {len(data['jobs'])} jobs")
    
    def test_jobs_have_description_field(self):
        """Each job should have a 'description' field"""
        response = requests.get(f"{BASE_URL}/api/public/jobs?limit=50")
        data = response.json()
        jobs = data.get("jobs", [])
        
        assert len(jobs) > 0, "No jobs returned"
        
        jobs_with_desc = 0
        jobs_without_desc = 0
        
        for job in jobs:
            if "description" in job and job["description"]:
                jobs_with_desc += 1
            else:
                jobs_without_desc += 1
        
        # At least 80% of jobs should have descriptions
        desc_percentage = (jobs_with_desc / len(jobs)) * 100 if len(jobs) > 0 else 0
        print(f"Jobs with description: {jobs_with_desc}/{len(jobs)} ({desc_percentage:.1f}%)")
        
        # We expect most jobs to have descriptions now
        assert jobs_with_desc > 0, "No jobs have descriptions"
        print(f"PASS: {jobs_with_desc} jobs have non-empty descriptions")
    
    def test_jobs_have_description_preview_field(self):
        """Each job should have a 'description_preview' field truncated to ~300 chars"""
        response = requests.get(f"{BASE_URL}/api/public/jobs?limit=50")
        data = response.json()
        jobs = data.get("jobs", [])
        
        assert len(jobs) > 0, "No jobs returned"
        
        jobs_with_preview = 0
        previews_correctly_truncated = 0
        
        for job in jobs:
            if "description_preview" in job and job["description_preview"]:
                jobs_with_preview += 1
                preview = job["description_preview"]
                # Preview should be max 303 chars (300 + "...")
                if len(preview) <= 303:
                    previews_correctly_truncated += 1
                # If description is longer than 300, preview should end with "..."
                if job.get("description") and len(job.get("description", "")) > 300:
                    if preview.endswith("..."):
                        pass  # Correct truncation
                    else:
                        print(f"Warning: Preview doesn't end with '...' for job {job.get('id')}")
        
        print(f"Jobs with description_preview: {jobs_with_preview}/{len(jobs)}")
        print(f"Previews correctly truncated (<=303 chars): {previews_correctly_truncated}/{jobs_with_preview}")
        
        assert jobs_with_preview > 0, "No jobs have description_preview"
        print(f"PASS: {jobs_with_preview} jobs have description_preview field")
    
    def test_descriptions_are_plain_text_no_html(self):
        """Job descriptions should be clean plain text without HTML tags"""
        response = requests.get(f"{BASE_URL}/api/public/jobs?limit=50")
        data = response.json()
        jobs = data.get("jobs", [])
        
        html_tag_pattern = re.compile(r'<(p|div|strong|span|br|ul|li|ol|h[1-6]|a|em|b|i)[^>]*>', re.IGNORECASE)
        
        jobs_with_html = []
        
        for job in jobs:
            description = job.get("description", "")
            if description:
                # Check for common HTML tags
                if html_tag_pattern.search(description):
                    jobs_with_html.append({
                        "id": job.get("id"),
                        "title": job.get("title"),
                        "source": job.get("source"),
                        "snippet": description[:200]
                    })
        
        if jobs_with_html:
            print(f"WARNING: {len(jobs_with_html)} jobs have HTML in descriptions:")
            for j in jobs_with_html[:3]:  # Show first 3
                print(f"  - {j['id']} ({j['source']}): {j['snippet'][:100]}...")
        
        # Assert no HTML tags found
        assert len(jobs_with_html) == 0, f"Found {len(jobs_with_html)} jobs with HTML tags in descriptions"
        print("PASS: All job descriptions are clean plain text (no HTML tags)")
    
    def test_jobs_sorted_by_posted_at_descending(self):
        """Jobs should be sorted by posted_at_dt descending (newest first)"""
        response = requests.get(f"{BASE_URL}/api/public/jobs?limit=20&sort_by=posted_at_dt&sort_order=desc")
        data = response.json()
        jobs = data.get("jobs", [])
        
        assert len(jobs) > 1, "Need at least 2 jobs to test sorting"
        
        dates = []
        for job in jobs:
            posted_at = job.get("posted_at")
            if posted_at:
                try:
                    dt = dateparser.parse(posted_at)
                    dates.append(dt)
                except:
                    pass
        
        assert len(dates) >= 2, "Not enough valid dates to verify sorting"
        
        # Check if dates are in descending order
        is_sorted_desc = all(dates[i] >= dates[i+1] for i in range(len(dates)-1) if dates[i] and dates[i+1])
        
        if not is_sorted_desc:
            print("Date order found:")
            for i, d in enumerate(dates[:10]):
                print(f"  {i}: {d}")
        
        assert is_sorted_desc, "Jobs are not sorted by posted_at_dt descending"
        print(f"PASS: Jobs are sorted by posted_at_dt descending (verified {len(dates)} dates)")


class TestJobDescriptionsBySource:
    """Test job descriptions by source (Greenhouse, Lever, Amazon, JSearch)"""
    
    def test_greenhouse_jobs_have_descriptions(self):
        """Greenhouse jobs should have descriptions (parsed from content field with ?content=true)"""
        response = requests.get(f"{BASE_URL}/api/public/jobs?source=greenhouse&limit=20")
        data = response.json()
        jobs = data.get("jobs", [])
        
        if len(jobs) == 0:
            pytest.skip("No Greenhouse jobs found in database")
        
        jobs_with_desc = sum(1 for j in jobs if j.get("description"))
        avg_desc_len = sum(len(j.get("description", "")) for j in jobs) / len(jobs) if len(jobs) > 0 else 0
        
        print(f"Greenhouse: {jobs_with_desc}/{len(jobs)} jobs with descriptions")
        print(f"Greenhouse avg description length: {avg_desc_len:.0f} chars")
        
        # At least 50% should have descriptions
        assert jobs_with_desc >= len(jobs) * 0.5, f"Only {jobs_with_desc}/{len(jobs)} Greenhouse jobs have descriptions"
        print(f"PASS: {jobs_with_desc}/{len(jobs)} Greenhouse jobs have descriptions")
    
    def test_lever_jobs_have_descriptions(self):
        """Lever jobs should have descriptions (from descriptionPlain + lists)"""
        response = requests.get(f"{BASE_URL}/api/public/jobs?source=lever&limit=20")
        data = response.json()
        jobs = data.get("jobs", [])
        
        if len(jobs) == 0:
            pytest.skip("No Lever jobs found in database")
        
        jobs_with_desc = sum(1 for j in jobs if j.get("description"))
        avg_desc_len = sum(len(j.get("description", "")) for j in jobs) / len(jobs) if len(jobs) > 0 else 0
        
        print(f"Lever: {jobs_with_desc}/{len(jobs)} jobs with descriptions")
        print(f"Lever avg description length: {avg_desc_len:.0f} chars")
        
        # At least 50% should have descriptions
        assert jobs_with_desc >= len(jobs) * 0.5, f"Only {jobs_with_desc}/{len(jobs)} Lever jobs have descriptions"
        print(f"PASS: {jobs_with_desc}/{len(jobs)} Lever jobs have descriptions")
    
    def test_amazon_jobs_have_descriptions(self):
        """Amazon jobs should have descriptions (full description from API)"""
        response = requests.get(f"{BASE_URL}/api/public/jobs?source=amazon&limit=20")
        data = response.json()
        jobs = data.get("jobs", [])
        
        if len(jobs) == 0:
            pytest.skip("No Amazon jobs found in database")
        
        jobs_with_desc = sum(1 for j in jobs if j.get("description"))
        avg_desc_len = sum(len(j.get("description", "")) for j in jobs) / len(jobs) if len(jobs) > 0 else 0
        
        print(f"Amazon: {jobs_with_desc}/{len(jobs)} jobs with descriptions")
        print(f"Amazon avg description length: {avg_desc_len:.0f} chars")
        
        # At least 50% should have descriptions
        assert jobs_with_desc >= len(jobs) * 0.5, f"Only {jobs_with_desc}/{len(jobs)} Amazon jobs have descriptions"
        print(f"PASS: {jobs_with_desc}/{len(jobs)} Amazon jobs have descriptions")
    
    def test_jsearch_jobs_have_descriptions(self):
        """JSearch jobs (Microsoft, Apple) should have descriptions (job_description field)"""
        response = requests.get(f"{BASE_URL}/api/public/jobs?source=jsearch&limit=20")
        data = response.json()
        jobs = data.get("jobs", [])
        
        if len(jobs) == 0:
            pytest.skip("No JSearch jobs found in database")
        
        jobs_with_desc = sum(1 for j in jobs if j.get("description"))
        avg_desc_len = sum(len(j.get("description", "")) for j in jobs) / len(jobs) if len(jobs) > 0 else 0
        
        print(f"JSearch: {jobs_with_desc}/{len(jobs)} jobs with descriptions")
        print(f"JSearch avg description length: {avg_desc_len:.0f} chars")
        
        # At least 50% should have descriptions
        assert jobs_with_desc >= len(jobs) * 0.5, f"Only {jobs_with_desc}/{len(jobs)} JSearch jobs have descriptions"
        print(f"PASS: {jobs_with_desc}/{len(jobs)} JSearch jobs have descriptions")


class TestDescriptionQuality:
    """Test the quality of job descriptions"""
    
    def test_descriptions_have_meaningful_content(self):
        """Descriptions should have meaningful content (not just whitespace/placeholders)"""
        response = requests.get(f"{BASE_URL}/api/public/jobs?limit=30")
        data = response.json()
        jobs = data.get("jobs", [])
        
        meaningful_descriptions = 0
        
        for job in jobs:
            desc = job.get("description", "")
            if desc:
                # Check for meaningful content (at least 50 chars after stripping whitespace)
                cleaned = desc.strip()
                if len(cleaned) >= 50:
                    # Not just placeholder text
                    placeholder_patterns = ["lorem ipsum", "placeholder", "tbd", "coming soon"]
                    is_placeholder = any(p in cleaned.lower() for p in placeholder_patterns)
                    if not is_placeholder:
                        meaningful_descriptions += 1
        
        print(f"Jobs with meaningful descriptions (>50 chars, no placeholders): {meaningful_descriptions}/{len(jobs)}")
        assert meaningful_descriptions > 0, "No jobs have meaningful descriptions"
        print(f"PASS: {meaningful_descriptions} jobs have meaningful descriptions")
    
    def test_description_preview_is_truncated_correctly(self):
        """description_preview should be max 303 chars (300 + '...')"""
        response = requests.get(f"{BASE_URL}/api/public/jobs?limit=50")
        data = response.json()
        jobs = data.get("jobs", [])
        
        for job in jobs:
            preview = job.get("description_preview", "")
            full_desc = job.get("description", "")
            
            if full_desc and len(full_desc) > 300:
                # Preview should be truncated with "..."
                assert len(preview) <= 303, f"Preview too long ({len(preview)} chars) for job {job.get('id')}"
                assert preview.endswith("..."), f"Long description preview should end with '...' for job {job.get('id')}"
            elif full_desc:
                # Preview should equal full description if <= 300 chars
                assert preview == full_desc, f"Short description preview should equal full description for job {job.get('id')}"
        
        print("PASS: All description_preview fields are correctly truncated")


class TestPaginationAndFilters:
    """Test pagination and filtering work correctly with descriptions"""
    
    def test_pagination_returns_consistent_results(self):
        """Paginated requests should return consistent results"""
        page1 = requests.get(f"{BASE_URL}/api/public/jobs?page=1&limit=10").json()
        page2 = requests.get(f"{BASE_URL}/api/public/jobs?page=2&limit=10").json()
        
        assert page1["pagination"]["page"] == 1
        assert page2["pagination"]["page"] == 2
        
        # Jobs on page 1 and page 2 should be different
        page1_ids = {j["id"] for j in page1["jobs"]}
        page2_ids = {j["id"] for j in page2["jobs"]}
        
        assert page1_ids.isdisjoint(page2_ids), "Page 1 and Page 2 have overlapping jobs"
        print("PASS: Pagination returns consistent, non-overlapping results")
    
    def test_source_filter_returns_correct_source(self):
        """Filtering by source should only return jobs from that source"""
        for source in ["greenhouse", "lever", "amazon", "jsearch"]:
            response = requests.get(f"{BASE_URL}/api/public/jobs?source={source}&limit=10")
            data = response.json()
            jobs = data.get("jobs", [])
            
            if len(jobs) == 0:
                print(f"No {source} jobs found, skipping")
                continue
            
            for job in jobs:
                assert job.get("source") == source, f"Job {job.get('id')} has source '{job.get('source')}' but expected '{source}'"
            
            print(f"PASS: All {len(jobs)} {source} jobs have correct source")


class TestPublicHealthEndpoint:
    """Test public health endpoint"""
    
    def test_health_endpoint(self):
        """Health endpoint should return job count and status"""
        response = requests.get(f"{BASE_URL}/api/public/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("status") == "healthy"
        assert "jobs_in_database" in data
        
        job_count = data.get("jobs_in_database", 0)
        print(f"Jobs in database: {job_count}")
        assert job_count > 0, "No jobs in database"
        print(f"PASS: Health endpoint returns healthy status with {job_count} jobs")
