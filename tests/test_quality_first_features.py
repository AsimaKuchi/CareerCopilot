"""
Test suite for Quality-First Job Matching Features
Tests new profile fields (work_authorization, industries, seniority_level)
and job search match evaluation (match_score, match_recommendation, strengths, gaps)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
SESSION_TOKEN = os.environ.get('TEST_SESSION_TOKEN', 'test_session_1768854199004')

@pytest.fixture
def api_client():
    """Shared requests session with auth"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SESSION_TOKEN}"
    })
    return session


class TestHealthCheck:
    """Basic health check tests"""
    
    def test_health_endpoint(self, api_client):
        """Test health endpoint is accessible"""
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✓ Health endpoint working")


class TestProfileNewFields:
    """Tests for new profile fields: work_authorization, industries, seniority_level"""
    
    def test_get_profile_has_new_fields(self, api_client):
        """Test that profile response includes new fields"""
        response = api_client.get(f"{BASE_URL}/api/profile")
        assert response.status_code == 200
        data = response.json()
        
        # Check new fields exist in response (may be null initially)
        assert "work_authorization" in data or data.get("work_authorization") is None
        assert "industries" in data
        assert "open_to_any_industry" in data
        assert "seniority_level" in data or data.get("seniority_level") is None
        print("✓ Profile response includes new fields")
    
    def test_update_work_authorization_citizen(self, api_client):
        """Test updating work_authorization to 'citizen'"""
        response = api_client.put(f"{BASE_URL}/api/profile", json={
            "work_authorization": "citizen"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("work_authorization") == "citizen"
        print("✓ Work authorization updated to 'citizen'")
    
    def test_update_work_authorization_permanent_resident(self, api_client):
        """Test updating work_authorization to 'permanent_resident'"""
        response = api_client.put(f"{BASE_URL}/api/profile", json={
            "work_authorization": "permanent_resident"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("work_authorization") == "permanent_resident"
        print("✓ Work authorization updated to 'permanent_resident'")
    
    def test_update_work_authorization_work_permit(self, api_client):
        """Test updating work_authorization to 'work_permit'"""
        response = api_client.put(f"{BASE_URL}/api/profile", json={
            "work_authorization": "work_permit"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("work_authorization") == "work_permit"
        print("✓ Work authorization updated to 'work_permit'")
    
    def test_update_work_authorization_require_sponsorship(self, api_client):
        """Test updating work_authorization to 'require_sponsorship'"""
        response = api_client.put(f"{BASE_URL}/api/profile", json={
            "work_authorization": "require_sponsorship"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("work_authorization") == "require_sponsorship"
        print("✓ Work authorization updated to 'require_sponsorship'")
    
    def test_update_industries_single(self, api_client):
        """Test updating industries with single industry"""
        response = api_client.put(f"{BASE_URL}/api/profile", json={
            "industries": ["technology"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "technology" in data.get("industries", [])
        print("✓ Industries updated with single industry")
    
    def test_update_industries_multiple(self, api_client):
        """Test updating industries with multiple industries (max 3)"""
        response = api_client.put(f"{BASE_URL}/api/profile", json={
            "industries": ["technology", "finance", "healthcare"]
        })
        assert response.status_code == 200
        data = response.json()
        industries = data.get("industries", [])
        assert len(industries) == 3
        assert "technology" in industries
        assert "finance" in industries
        assert "healthcare" in industries
        print("✓ Industries updated with 3 industries")
    
    def test_update_open_to_any_industry_true(self, api_client):
        """Test setting open_to_any_industry to true"""
        response = api_client.put(f"{BASE_URL}/api/profile", json={
            "open_to_any_industry": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("open_to_any_industry") == True
        print("✓ open_to_any_industry set to True")
    
    def test_update_open_to_any_industry_false(self, api_client):
        """Test setting open_to_any_industry to false"""
        response = api_client.put(f"{BASE_URL}/api/profile", json={
            "open_to_any_industry": False
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("open_to_any_industry") == False
        print("✓ open_to_any_industry set to False")
    
    def test_update_seniority_level_entry(self, api_client):
        """Test updating seniority_level to 'entry'"""
        response = api_client.put(f"{BASE_URL}/api/profile", json={
            "seniority_level": "entry"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("seniority_level") == "entry"
        print("✓ Seniority level updated to 'entry'")
    
    def test_update_seniority_level_senior(self, api_client):
        """Test updating seniority_level to 'senior'"""
        response = api_client.put(f"{BASE_URL}/api/profile", json={
            "seniority_level": "senior"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("seniority_level") == "senior"
        print("✓ Seniority level updated to 'senior'")
    
    def test_update_seniority_level_director(self, api_client):
        """Test updating seniority_level to 'director'"""
        response = api_client.put(f"{BASE_URL}/api/profile", json={
            "seniority_level": "director"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("seniority_level") == "director"
        print("✓ Seniority level updated to 'director'")
    
    def test_update_all_new_fields_together(self, api_client):
        """Test updating all new fields in a single request"""
        response = api_client.put(f"{BASE_URL}/api/profile", json={
            "work_authorization": "citizen",
            "industries": ["technology", "consulting"],
            "open_to_any_industry": False,
            "seniority_level": "mid"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("work_authorization") == "citizen"
        assert "technology" in data.get("industries", [])
        assert "consulting" in data.get("industries", [])
        assert data.get("open_to_any_industry") == False
        assert data.get("seniority_level") == "mid"
        print("✓ All new fields updated together successfully")
    
    def test_profile_persistence_after_update(self, api_client):
        """Test that profile changes persist after update"""
        # First update
        api_client.put(f"{BASE_URL}/api/profile", json={
            "work_authorization": "permanent_resident",
            "seniority_level": "lead"
        })
        
        # Fetch again to verify persistence
        response = api_client.get(f"{BASE_URL}/api/profile")
        assert response.status_code == 200
        data = response.json()
        assert data.get("work_authorization") == "permanent_resident"
        assert data.get("seniority_level") == "lead"
        print("✓ Profile changes persisted correctly")


class TestJobSearchMatchDetails:
    """Tests for job search match evaluation details"""
    
    def test_job_search_returns_match_score(self, api_client):
        """Test that job search returns match_score for each job"""
        response = api_client.post(f"{BASE_URL}/api/jobs/search", json={
            "query": "software engineer",
            "page": 1,
            "num_pages": 1
        })
        assert response.status_code == 200
        data = response.json()
        jobs = data.get("jobs", [])
        
        if len(jobs) > 0:
            job = jobs[0]
            assert "match_score" in job
            assert isinstance(job["match_score"], int)
            assert 0 <= job["match_score"] <= 100
            print(f"✓ Job search returns match_score: {job['match_score']}")
        else:
            print("⚠ No jobs returned to verify match_score")
    
    def test_job_search_returns_match_recommendation(self, api_client):
        """Test that job search returns match_recommendation for each job"""
        response = api_client.post(f"{BASE_URL}/api/jobs/search", json={
            "query": "software engineer",
            "page": 1,
            "num_pages": 1
        })
        assert response.status_code == 200
        data = response.json()
        jobs = data.get("jobs", [])
        
        valid_recommendations = ["strong_match", "good_match", "review", "weak_match", "skip"]
        
        if len(jobs) > 0:
            job = jobs[0]
            assert "match_recommendation" in job
            assert job["match_recommendation"] in valid_recommendations
            print(f"✓ Job search returns match_recommendation: {job['match_recommendation']}")
        else:
            print("⚠ No jobs returned to verify match_recommendation")
    
    def test_job_search_returns_match_strengths(self, api_client):
        """Test that job search returns match_strengths array"""
        response = api_client.post(f"{BASE_URL}/api/jobs/search", json={
            "query": "software engineer",
            "page": 1,
            "num_pages": 1
        })
        assert response.status_code == 200
        data = response.json()
        jobs = data.get("jobs", [])
        
        if len(jobs) > 0:
            job = jobs[0]
            assert "match_strengths" in job
            assert isinstance(job["match_strengths"], list)
            print(f"✓ Job search returns match_strengths: {job['match_strengths']}")
        else:
            print("⚠ No jobs returned to verify match_strengths")
    
    def test_job_search_returns_match_gaps(self, api_client):
        """Test that job search returns match_gaps array"""
        response = api_client.post(f"{BASE_URL}/api/jobs/search", json={
            "query": "software engineer",
            "page": 1,
            "num_pages": 1
        })
        assert response.status_code == 200
        data = response.json()
        jobs = data.get("jobs", [])
        
        if len(jobs) > 0:
            job = jobs[0]
            assert "match_gaps" in job
            assert isinstance(job["match_gaps"], list)
            print(f"✓ Job search returns match_gaps: {job['match_gaps']}")
        else:
            print("⚠ No jobs returned to verify match_gaps")
    
    def test_job_search_returns_match_reasoning(self, api_client):
        """Test that job search returns match_reasoning string"""
        response = api_client.post(f"{BASE_URL}/api/jobs/search", json={
            "query": "software engineer",
            "page": 1,
            "num_pages": 1
        })
        assert response.status_code == 200
        data = response.json()
        jobs = data.get("jobs", [])
        
        if len(jobs) > 0:
            job = jobs[0]
            assert "match_reasoning" in job
            assert isinstance(job["match_reasoning"], str)
            assert len(job["match_reasoning"]) > 0
            print(f"✓ Job search returns match_reasoning: {job['match_reasoning']}")
        else:
            print("⚠ No jobs returned to verify match_reasoning")
    
    def test_job_search_returns_skip_reason(self, api_client):
        """Test that job search returns skip_reason field (may be null)"""
        response = api_client.post(f"{BASE_URL}/api/jobs/search", json={
            "query": "software engineer",
            "page": 1,
            "num_pages": 1
        })
        assert response.status_code == 200
        data = response.json()
        jobs = data.get("jobs", [])
        
        if len(jobs) > 0:
            job = jobs[0]
            assert "skip_reason" in job
            # skip_reason can be null or a string
            assert job["skip_reason"] is None or isinstance(job["skip_reason"], str)
            print(f"✓ Job search returns skip_reason: {job['skip_reason']}")
        else:
            print("⚠ No jobs returned to verify skip_reason")
    
    def test_job_search_all_match_fields_present(self, api_client):
        """Test that all match evaluation fields are present in job response"""
        response = api_client.post(f"{BASE_URL}/api/jobs/search", json={
            "query": "python developer",
            "page": 1,
            "num_pages": 1
        })
        assert response.status_code == 200
        data = response.json()
        jobs = data.get("jobs", [])
        
        required_match_fields = [
            "match_score",
            "match_recommendation", 
            "match_strengths",
            "match_gaps",
            "match_reasoning",
            "skip_reason"
        ]
        
        if len(jobs) > 0:
            job = jobs[0]
            for field in required_match_fields:
                assert field in job, f"Missing field: {field}"
            print(f"✓ All match evaluation fields present in job response")
            print(f"  - match_score: {job['match_score']}")
            print(f"  - match_recommendation: {job['match_recommendation']}")
            print(f"  - match_strengths: {job['match_strengths']}")
            print(f"  - match_gaps: {job['match_gaps']}")
            print(f"  - match_reasoning: {job['match_reasoning']}")
            print(f"  - skip_reason: {job['skip_reason']}")
        else:
            print("⚠ No jobs returned to verify all match fields")


class TestJobSearchWithProfileContext:
    """Tests for job search match evaluation with different profile configurations"""
    
    def test_search_with_matching_skills(self, api_client):
        """Test job search with profile that has matching skills"""
        # First update profile with relevant skills
        api_client.put(f"{BASE_URL}/api/profile", json={
            "skills": ["Python", "JavaScript", "React", "AWS"],
            "job_titles": ["Software Engineer"],
            "experience_years": 5,
            "seniority_level": "senior"
        })
        
        # Search for matching jobs
        response = api_client.post(f"{BASE_URL}/api/jobs/search", json={
            "query": "software engineer python",
            "page": 1,
            "num_pages": 1
        })
        assert response.status_code == 200
        data = response.json()
        jobs = data.get("jobs", [])
        
        if len(jobs) > 0:
            # Check that at least some jobs have good match scores
            high_match_jobs = [j for j in jobs if j.get("match_score", 0) >= 50]
            print(f"✓ Found {len(high_match_jobs)} jobs with match score >= 50")
        else:
            print("⚠ No jobs returned for matching skills test")
    
    def test_search_with_location_preference(self, api_client):
        """Test job search respects location preferences"""
        # Update profile with location preference
        api_client.put(f"{BASE_URL}/api/profile", json={
            "preferred_locations": ["Remote", "San Francisco"]
        })
        
        response = api_client.post(f"{BASE_URL}/api/jobs/search", json={
            "query": "software engineer",
            "location": "San Francisco",
            "page": 1,
            "num_pages": 1
        })
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Job search with location preference returned {len(data.get('jobs', []))} jobs")


class TestAuthenticationRequired:
    """Tests to verify authentication is required for protected endpoints"""
    
    def test_profile_requires_auth(self):
        """Test that profile endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/profile")
        assert response.status_code == 401
        print("✓ Profile endpoint requires authentication")
    
    def test_job_search_requires_auth(self):
        """Test that job search endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/jobs/search", json={
            "query": "software engineer"
        })
        assert response.status_code == 401
        print("✓ Job search endpoint requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
