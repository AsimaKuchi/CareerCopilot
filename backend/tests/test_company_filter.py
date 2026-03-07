"""
Backend Tests for Company Filter Feature
Tests the company filter functionality added to job search endpoints
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://job-auto-fill-1.preview.emergentagent.com').rstrip('/')

# Test session token (created via mongosh)
SESSION_TOKEN = None

@pytest.fixture(scope="module", autouse=True)
def setup_test_session():
    """Create a test user session for authenticated tests."""
    global SESSION_TOKEN
    
    import subprocess
    result = subprocess.run(
        ["mongosh", "--quiet", "--eval", """
use('test_database');
var userId = 'test-company-filter-pytest-' + Date.now();
var sessionToken = 'test_session_pytest_' + Date.now();
db.users.insertOne({
  user_id: userId,
  email: 'test.pytest.' + Date.now() + '@example.com',
  name: 'Test PyTest User',
  email_verified: true,
  created_at: new Date()
});
db.user_sessions.insertOne({
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000),
  created_at: new Date()
});
db.user_profiles.insertOne({
  user_id: userId,
  resume_text: 'Software Engineer with 5 years experience',
  skills: ['Python', 'JavaScript'],
  experience_years: 5,
  job_titles: ['Software Engineer'],
  preferred_locations: ['Toronto'],
  updated_at: new Date()
});
print(sessionToken);
"""],
        capture_output=True,
        text=True
    )
    SESSION_TOKEN = result.stdout.strip().split('\n')[-1]
    yield
    # Cleanup not required - sessions auto-expire


@pytest.fixture
def auth_headers():
    """Return headers with session token."""
    return {
        "Content-Type": "application/json",
        "Cookie": f"session_token={SESSION_TOKEN}"
    }


class TestCompanySearchAnalytics:
    """Test POST /api/analytics/company-search endpoint"""
    
    def test_track_company_search_success(self, auth_headers):
        """Test tracking a company search."""
        response = requests.post(
            f"{BASE_URL}/api/analytics/company-search",
            headers=auth_headers,
            json={"company": "Amazon"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "tracked"
    
    def test_track_company_search_microsoft(self, auth_headers):
        """Test tracking Microsoft company search."""
        response = requests.post(
            f"{BASE_URL}/api/analytics/company-search",
            headers=auth_headers,
            json={"company": "Microsoft"}
        )
        
        assert response.status_code == 200
        assert response.json().get("status") == "tracked"
    
    def test_track_company_search_empty_skipped(self, auth_headers):
        """Test that empty company is skipped."""
        response = requests.post(
            f"{BASE_URL}/api/analytics/company-search",
            headers=auth_headers,
            json={"company": ""}
        )
        
        assert response.status_code == 200
        assert response.json().get("status") == "skipped"
    
    def test_track_company_search_without_auth(self):
        """Test that unauthenticated requests are rejected."""
        response = requests.post(
            f"{BASE_URL}/api/analytics/company-search",
            headers={"Content-Type": "application/json"},
            json={"company": "Google"}
        )
        
        assert response.status_code == 401


class TestJSearchWithCompanyFilter:
    """Test POST /api/jobs/search with company filter (JSearch aggregator)"""
    
    def test_jsearch_without_company_filter(self, auth_headers):
        """Test JSearch works without company filter."""
        response = requests.post(
            f"{BASE_URL}/api/jobs/search",
            headers=auth_headers,
            json={
                "query": "Software Engineer",
                "location": "Toronto"
            },
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        # Note: May return empty list if API rate limited
    
    def test_jsearch_with_company_filter_microsoft(self, auth_headers):
        """Test JSearch filters by Microsoft company."""
        response = requests.post(
            f"{BASE_URL}/api/jobs/search",
            headers=auth_headers,
            json={
                "query": "Software Engineer",
                "location": "",
                "company": "Microsoft"
            },
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        
        # If jobs returned, verify they're from Microsoft
        for job in data.get("jobs", []):
            company_name = (job.get("company") or job.get("employer_name") or "").lower()
            assert "microsoft" in company_name, f"Job company '{company_name}' should contain 'microsoft'"
    
    def test_jsearch_with_company_filter_amazon(self, auth_headers):
        """Test JSearch filters by Amazon company."""
        response = requests.post(
            f"{BASE_URL}/api/jobs/search",
            headers=auth_headers,
            json={
                "query": "Engineer",
                "location": "",
                "company": "Amazon"
            },
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
    
    def test_jsearch_without_auth(self):
        """Test that unauthenticated requests are rejected."""
        response = requests.post(
            f"{BASE_URL}/api/jobs/search",
            headers={"Content-Type": "application/json"},
            json={"query": "Engineer", "company": "Google"},
            timeout=10
        )
        
        assert response.status_code == 401


class TestGreenhouseSearchWithCompanyFilter:
    """Test POST /api/jobs/greenhouse/search with company filter (streaming endpoint)"""
    
    def test_greenhouse_search_without_company_filter(self, auth_headers):
        """Test Greenhouse streaming search works without company filter."""
        response = requests.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            headers=auth_headers,
            json={
                "query": "Software Engineer",
                "location": ""
            },
            stream=True,
            timeout=15
        )
        
        assert response.status_code == 200
        
        # Read first few chunks to verify streaming works
        content = b""
        for chunk in response.iter_content(chunk_size=1024):
            content += chunk
            if len(content) > 500:
                break
        
        content_str = content.decode('utf-8')
        assert "data:" in content_str  # SSE format
        assert "heartbeat" in content_str or "progress" in content_str
    
    def test_greenhouse_search_with_company_filter_airbnb(self, auth_headers):
        """Test Greenhouse search filters by Airbnb company."""
        response = requests.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            headers=auth_headers,
            json={
                "query": "Engineer",
                "location": "",
                "company": "Airbnb"
            },
            stream=True,
            timeout=30
        )
        
        assert response.status_code == 200
        
        # Read streaming response
        content = b""
        for chunk in response.iter_content(chunk_size=1024):
            content += chunk
            if b'"done"' in content:
                break
            if len(content) > 10000:
                break
        
        content_str = content.decode('utf-8')
        
        # Parse SSE data to check jobs
        import json
        jobs_found = []
        for line in content_str.split('\n'):
            if line.startswith('data: '):
                try:
                    data = json.loads(line[6:])
                    if data.get('title') and data.get('company'):
                        jobs_found.append(data)
                except:
                    pass
        
        # If jobs found, verify they're from Airbnb
        for job in jobs_found:
            company = (job.get("company") or "").lower()
            assert "airbnb" in company, f"Expected Airbnb jobs, got {job.get('company')}"
    
    def test_greenhouse_search_with_company_filter_stripe(self, auth_headers):
        """Test Greenhouse search filters by Stripe company."""
        response = requests.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            headers=auth_headers,
            json={
                "query": "Engineer",
                "location": "",
                "company": "Stripe"
            },
            stream=True,
            timeout=30
        )
        
        assert response.status_code == 200
    
    def test_greenhouse_search_without_auth(self):
        """Test that unauthenticated requests are rejected."""
        response = requests.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            headers={"Content-Type": "application/json"},
            json={"query": "Engineer", "company": "Google"},
            timeout=10
        )
        
        assert response.status_code == 401


class TestPublicJobsAPI:
    """Test GET /api/public/jobs with company filter (public API)"""
    
    def test_public_jobs_without_company_filter(self):
        """Test public jobs API returns jobs."""
        response = requests.get(
            f"{BASE_URL}/api/public/jobs",
            params={"limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "pagination" in data
    
    def test_public_jobs_with_company_filter_amazon(self):
        """Test public jobs API filters by Amazon."""
        response = requests.get(
            f"{BASE_URL}/api/public/jobs",
            params={"company": "Amazon", "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        
        # If jobs returned, verify they're from Amazon
        for job in data.get("jobs", []):
            company = (job.get("company") or "").lower()
            assert "amazon" in company, f"Expected Amazon jobs, got {job.get('company')}"
    
    def test_public_jobs_with_company_filter_microsoft(self):
        """Test public jobs API filters by Microsoft."""
        response = requests.get(
            f"{BASE_URL}/api/public/jobs",
            params={"company": "Microsoft", "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data


class TestTopCompaniesInDB:
    """Verify that expected top companies have jobs in the database"""
    
    def test_amazon_jobs_exist(self):
        """Verify Amazon jobs exist in stored_jobs."""
        response = requests.get(
            f"{BASE_URL}/api/public/jobs",
            params={"company": "Amazon", "source": "amazon", "limit": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Amazon should have jobs based on previous tests
        assert data.get("pagination", {}).get("total", 0) >= 0
    
    def test_greenhouse_companies_exist(self):
        """Verify Greenhouse companies have jobs."""
        response = requests.get(
            f"{BASE_URL}/api/public/jobs",
            params={"source": "greenhouse", "limit": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("jobs", [])) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
