"""
Test Job Sources - Amazon, Microsoft, Apple Jobs Integration
Tests for the new job sources: Amazon (direct API), Microsoft/Apple (via JSearch)
Also tests GET /api/public/sources and GET /api/public/jobs endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://job-auto-fill-1.preview.emergentagent.com"


@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


class TestHealthCheck:
    """Basic API health check"""
    
    def test_api_health(self, api_client):
        """Test that API is reachable"""
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"


class TestJobSources:
    """Tests for GET /api/public/sources endpoint"""
    
    def test_sources_returns_expected_sources(self, api_client):
        """Verify amazon and jsearch are listed as sources with non-zero counts"""
        response = api_client.get(f"{BASE_URL}/api/public/sources")
        assert response.status_code == 200
        
        data = response.json()
        assert "sources" in data
        assert "total_jobs" in data
        
        sources = data["sources"]
        source_names = {s["source"] for s in sources}
        
        # Must have amazon and jsearch
        assert "amazon" in source_names, f"amazon not in sources: {source_names}"
        assert "jsearch" in source_names, f"jsearch not in sources: {source_names}"
        
        # Get counts
        amazon_source = next((s for s in sources if s["source"] == "amazon"), None)
        jsearch_source = next((s for s in sources if s["source"] == "jsearch"), None)
        
        assert amazon_source is not None
        assert jsearch_source is not None
        assert amazon_source["job_count"] > 0, "Amazon should have jobs"
        assert jsearch_source["job_count"] > 0, "JSearch should have jobs"
        
        print(f"Amazon jobs: {amazon_source['job_count']}")
        print(f"JSearch jobs: {jsearch_source['job_count']}")
    
    def test_sources_total_count_matches_sum(self, api_client):
        """Verify total_jobs equals sum of all source counts"""
        response = api_client.get(f"{BASE_URL}/api/public/sources")
        assert response.status_code == 200
        
        data = response.json()
        sources = data["sources"]
        expected_total = sum(s["job_count"] for s in sources)
        
        assert data["total_jobs"] == expected_total


class TestAmazonJobs:
    """Tests for Amazon jobs in stored_jobs collection"""
    
    def test_amazon_jobs_exist(self, api_client):
        """Verify Amazon jobs exist with source='amazon'"""
        response = api_client.get(f"{BASE_URL}/api/public/jobs?source=amazon&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "jobs" in data
        assert len(data["jobs"]) > 0, "Should have Amazon jobs"
        
        # All jobs should have source=amazon
        for job in data["jobs"]:
            assert job["source"] == "amazon"
    
    def test_amazon_jobs_have_required_fields(self, api_client):
        """Verify Amazon jobs have correct fields"""
        response = api_client.get(f"{BASE_URL}/api/public/jobs?source=amazon&limit=5")
        assert response.status_code == 200
        
        data = response.json()
        jobs = data["jobs"]
        assert len(jobs) > 0
        
        for job in jobs:
            # Required fields
            assert "title" in job and job["title"], f"Missing title: {job}"
            assert "company" in job and job["company"], f"Missing company: {job}"
            assert "location" in job and job["location"], f"Missing location: {job}"
            assert "apply_url" in job and job["apply_url"], f"Missing apply_url: {job}"
            
            # Company should be Amazon
            assert "Amazon" in job["company"] or job["company"] == "Amazon", f"Company not Amazon: {job['company']}"
    
    def test_amazon_jobs_count(self, api_client):
        """Verify Amazon has a reasonable number of jobs (expected ~120)"""
        response = api_client.get(f"{BASE_URL}/api/public/jobs?source=amazon&limit=1")
        assert response.status_code == 200
        
        data = response.json()
        total = data["pagination"]["total"]
        
        # Should have at least 50 Amazon jobs
        assert total >= 50, f"Expected at least 50 Amazon jobs, got {total}"
        print(f"Total Amazon jobs: {total}")


class TestMicrosoftJobs:
    """Tests for Microsoft jobs via JSearch"""
    
    def test_microsoft_jobs_exist(self, api_client):
        """Verify Microsoft jobs exist with company containing 'Microsoft'"""
        response = api_client.get(f"{BASE_URL}/api/public/jobs?company=Microsoft&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        jobs = data["jobs"]
        
        # Filter to only Microsoft company jobs
        microsoft_jobs = [j for j in jobs if "Microsoft" in j.get("company", "")]
        assert len(microsoft_jobs) > 0, "Should have Microsoft jobs"
        
        print(f"Found {len(microsoft_jobs)} Microsoft jobs in result")
    
    def test_microsoft_jobs_have_required_fields(self, api_client):
        """Verify Microsoft jobs have correct fields"""
        response = api_client.get(f"{BASE_URL}/api/public/jobs?company=Microsoft&limit=5")
        assert response.status_code == 200
        
        data = response.json()
        jobs = [j for j in data["jobs"] if "Microsoft" in j.get("company", "")]
        
        for job in jobs:
            assert "title" in job and job["title"]
            assert "company" in job
            assert "Microsoft" in job["company"]
            assert "apply_url" in job
    
    def test_microsoft_jobs_via_jsearch(self, api_client):
        """Verify Microsoft jobs come from jsearch source"""
        response = api_client.get(f"{BASE_URL}/api/public/jobs?source=jsearch&limit=50")
        assert response.status_code == 200
        
        data = response.json()
        jobs = data["jobs"]
        
        microsoft_jobs = [j for j in jobs if "Microsoft" in j.get("company", "")]
        assert len(microsoft_jobs) > 0, "Should have Microsoft jobs from jsearch"
        
        for job in microsoft_jobs:
            assert job["source"] == "jsearch"


class TestAppleJobs:
    """Tests for Apple jobs via JSearch"""
    
    def test_apple_jobs_exist(self, api_client):
        """Verify Apple jobs exist with company containing 'Apple'"""
        response = api_client.get(f"{BASE_URL}/api/public/jobs?company=Apple&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        jobs = data["jobs"]
        
        # Filter to only Apple company jobs
        apple_jobs = [j for j in jobs if "Apple" in j.get("company", "")]
        assert len(apple_jobs) > 0, "Should have Apple jobs"
        
        print(f"Found {len(apple_jobs)} Apple jobs in result")
    
    def test_apple_jobs_have_required_fields(self, api_client):
        """Verify Apple jobs have correct fields"""
        response = api_client.get(f"{BASE_URL}/api/public/jobs?company=Apple&limit=5")
        assert response.status_code == 200
        
        data = response.json()
        jobs = [j for j in data["jobs"] if "Apple" in j.get("company", "")]
        
        for job in jobs:
            assert "title" in job and job["title"]
            assert "company" in job
            assert "Apple" in job["company"]
            assert "apply_url" in job
    
    def test_apple_jobs_via_jsearch(self, api_client):
        """Verify Apple jobs come from jsearch source"""
        response = api_client.get(f"{BASE_URL}/api/public/jobs?source=jsearch&limit=50")
        assert response.status_code == 200
        
        data = response.json()
        jobs = data["jobs"]
        
        apple_jobs = [j for j in jobs if "Apple" in j.get("company", "")]
        assert len(apple_jobs) > 0, "Should have Apple jobs from jsearch"
        
        for job in apple_jobs:
            assert job["source"] == "jsearch"


class TestJobsPublicAPI:
    """Tests for GET /api/public/jobs endpoint"""
    
    def test_get_jobs_returns_amazon_in_results(self, api_client):
        """Verify GET /api/public/jobs returns jobs from Amazon"""
        response = api_client.get(f"{BASE_URL}/api/public/jobs?limit=100")
        assert response.status_code == 200
        
        data = response.json()
        jobs = data["jobs"]
        
        # Look for Amazon jobs in unfiltered results
        amazon_jobs = [j for j in jobs if j.get("source") == "amazon"]
        # May or may not appear in first 100 jobs, but if filter works it should be findable
        
        # Try direct filter
        response2 = api_client.get(f"{BASE_URL}/api/public/jobs?source=amazon&limit=5")
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["jobs"]) > 0, "Amazon jobs should be available via filter"
    
    def test_jobs_pagination(self, api_client):
        """Test pagination parameters work"""
        response = api_client.get(f"{BASE_URL}/api/public/jobs?page=1&limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["jobs"]) <= 5
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["limit"] == 5
        assert data["pagination"]["total"] > 0
    
    def test_jobs_source_filter(self, api_client):
        """Test source filter parameter"""
        for source in ["amazon", "jsearch", "greenhouse", "lever"]:
            response = api_client.get(f"{BASE_URL}/api/public/jobs?source={source}&limit=5")
            assert response.status_code == 200
            
            data = response.json()
            if data["pagination"]["total"] > 0:
                for job in data["jobs"]:
                    assert job["source"] == source


class TestIngestEndpoint:
    """Tests for POST /api/public/jobs/ingest endpoint"""
    
    def test_ingest_endpoint_accepts_background_mode(self, api_client):
        """Verify POST /api/public/jobs/ingest starts in background mode"""
        response = api_client.post(f"{BASE_URL}/api/public/jobs/ingest?background=true")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("status") == "started"
        assert "background" in data.get("message", "").lower()
    
    def test_ingest_endpoint_exists(self, api_client):
        """Verify the ingest endpoint is reachable"""
        # Just verify it doesn't 404 - we use background mode to avoid long wait
        response = api_client.post(f"{BASE_URL}/api/public/jobs/ingest?background=true")
        assert response.status_code == 200


class TestJSearchJobsTotal:
    """Tests to verify total JSearch jobs count"""
    
    def test_jsearch_has_expected_job_count(self, api_client):
        """Verify JSearch has approximately 30 jobs (14 Microsoft + 16 Apple)"""
        response = api_client.get(f"{BASE_URL}/api/public/jobs?source=jsearch&limit=1")
        assert response.status_code == 200
        
        data = response.json()
        total = data["pagination"]["total"]
        
        # Should have at least 20 JSearch jobs (Microsoft + Apple combined)
        assert total >= 20, f"Expected at least 20 JSearch jobs, got {total}"
        print(f"Total JSearch jobs: {total}")
    
    def test_jsearch_contains_both_companies(self, api_client):
        """Verify JSearch contains both Microsoft and Apple jobs"""
        response = api_client.get(f"{BASE_URL}/api/public/jobs?source=jsearch&limit=50")
        assert response.status_code == 200
        
        data = response.json()
        jobs = data["jobs"]
        
        companies = set(j.get("company", "") for j in jobs)
        company_str = " ".join(companies)
        
        has_microsoft = "Microsoft" in company_str
        has_apple = "Apple" in company_str
        
        assert has_microsoft, f"JSearch should have Microsoft jobs. Companies: {companies}"
        assert has_apple, f"JSearch should have Apple jobs. Companies: {companies}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
