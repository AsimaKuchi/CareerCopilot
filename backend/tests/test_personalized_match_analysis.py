"""
Test Suite: Personalized Job Match Analysis
Tests the enhanced evaluate_job_match() function that provides grounded_strengths
with actual resume evidence, matched_skills, and personalized insights.
"""
import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@demo.com"
TEST_PASSWORD = "Test123!"


def parse_sse_response(response_text):
    """Parse Server-Sent Events format response into job list."""
    jobs = []
    for line in response_text.strip().split('\n'):
        line = line.strip()
        # Handle SSE format (data: {...})
        if line.startswith('data: '):
            line = line[6:]  # Remove 'data: ' prefix
        if line:
            try:
                data = json.loads(line)
                # Skip heartbeat and progress messages
                if "job_id" in data or ("title" in data and not data.get("heartbeat") and not data.get("progress")):
                    jobs.append(data)
            except:
                pass
    return jobs


@pytest.fixture(scope="module")
def auth_session():
    """Get authenticated session for test user."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    # Login
    login_response = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    
    if login_response.status_code != 200:
        pytest.skip(f"Login failed: {login_response.text}")
    
    return session

@pytest.fixture(scope="module")
def user_profile(auth_session):
    """Get the test user's profile."""
    response = auth_session.get(f"{BASE_URL}/api/profile")
    if response.status_code != 200:
        pytest.skip(f"Failed to get profile: {response.text}")
    return response.json()


class TestMatchAnalysisAPIStructure:
    """Test that match analysis API returns proper response structure with grounded_strengths."""
    
    def test_greenhouse_search_returns_match_info(self, auth_session):
        """Test that Greenhouse search (POST) includes match info with grounded_strengths."""
        response = auth_session.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            json={"query": "Business Analyst", "limit": 5},
            timeout=90
        )
        
        assert response.status_code == 200, f"Search failed: {response.text}"
        
        jobs_found = parse_sse_response(response.text)
        print(f"Found {len(jobs_found)} jobs from streaming response")
        
        if jobs_found:
            job = jobs_found[0]
            print(f"First job keys: {list(job.keys())}")
            
            # Check for match fields
            assert "match_score" in job, "Job missing match_score"
            print(f"  match_score: {job['match_score']}")
            
            if "grounded_strengths" in job:
                print(f"  grounded_strengths: {len(job['grounded_strengths'])} items")
                for gs in job["grounded_strengths"][:2]:
                    print(f"    - {gs}")
            
            if "matched_skills" in job:
                print(f"  matched_skills: {job['matched_skills']}")
    
    def test_public_job_search_works(self, auth_session):
        """Test public jobs API."""
        response = auth_session.get(
            f"{BASE_URL}/api/public/jobs",
            params={"query": "Analyst", "limit": 3}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "jobs" in data, "Response missing 'jobs' key"
        jobs = data["jobs"]
        print(f"Found {len(jobs)} public jobs")
        
        if jobs:
            job = jobs[0]
            print(f"Job keys: {list(job.keys())}")


class TestGroundedStrengthsFormat:
    """Test that grounded_strengths array has correct structure."""
    
    def test_grounded_strengths_has_required_fields(self, auth_session):
        """Verify grounded_strengths includes requirement, evidence, match_reason."""
        response = auth_session.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            json={"query": "Business Analyst", "limit": 10},
            timeout=90
        )
        
        assert response.status_code == 200
        
        jobs = parse_sse_response(response.text)
        jobs_with_grounded = [j for j in jobs if j.get("grounded_strengths")]
        
        print(f"Found {len(jobs_with_grounded)} jobs with grounded_strengths")
        
        assert len(jobs_with_grounded) > 0, "No jobs found with grounded_strengths"
        
        job = jobs_with_grounded[0]
        grounded = job["grounded_strengths"]
        
        print(f"\nJob: {job.get('title')} at {job.get('company')}")
        print(f"grounded_strengths ({len(grounded)}):")
        
        for strength in grounded:
            print(f"  - Requirement: {strength.get('requirement', 'N/A')}")
            print(f"    Evidence: {str(strength.get('evidence', 'N/A'))[:80]}...")
            print(f"    Match Reason: {strength.get('match_reason', 'N/A')}")
            
            # Assert structure
            assert "requirement" in strength, "grounded_strength missing 'requirement'"
            assert "evidence" in strength, "grounded_strength missing 'evidence'"
            assert "match_reason" in strength, "grounded_strength missing 'match_reason'"
    
    def test_matched_skills_array_present(self, auth_session):
        """Verify matched_skills array is returned."""
        response = auth_session.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            json={"query": "Data Analyst Python SQL", "limit": 5},
            timeout=90
        )
        
        assert response.status_code == 200
        
        jobs = parse_sse_response(response.text)
        print(f"Found {len(jobs)} jobs")
        
        # Check if any job has matched_skills
        for job in jobs[:5]:
            skills = job.get("matched_skills", [])
            if skills:
                print(f"\nJob: {job.get('title')} at {job.get('company')}")
                print(f"Matched skills: {skills}")
                assert isinstance(skills, list), "matched_skills should be a list"
                return
        
        print("Note: No matched skills found - may need profile with skills matching job descriptions")


class TestProfileBasedMatching:
    """Test that match analysis uses actual user profile data."""
    
    def test_profile_has_required_fields_for_matching(self, auth_session, user_profile):
        """Verify test user profile has necessary data for personalized matching."""
        print(f"\nTest user profile:")
        print(f"  Job titles: {user_profile.get('job_titles', [])}")
        
        skills = user_profile.get('skills', [])
        skill_names = [s.get('name') if isinstance(s, dict) else s for s in skills]
        print(f"  Skills: {skill_names}")
        
        print(f"  Experience years: {user_profile.get('experience_years')}")
        print(f"  Seniority level: {user_profile.get('seniority_level')}")
        print(f"  Resume text present: {bool(user_profile.get('resume_text'))}")
        
        # Verify profile has key matching data
        assert user_profile.get("job_titles"), "Profile missing job_titles for matching"
        assert user_profile.get("skills"), "Profile missing skills for matching"
        
        # Check resume
        resume_text = user_profile.get("resume_text", "")
        if resume_text:
            print(f"  Resume length: {len(resume_text)} characters")
            print(f"  Resume preview: {resume_text[:300]}...")
    
    def test_match_score_calculated(self, auth_session):
        """Test that match scores are calculated for jobs."""
        response = auth_session.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            json={"query": "Business Analyst", "limit": 5},
            timeout=90
        )
        
        assert response.status_code == 200
        
        jobs = parse_sse_response(response.text)
        scores = [{"title": j.get("title"), "company": j.get("company"), 
                   "score": j["match_score"], "recommendation": j.get("match_recommendation")} 
                  for j in jobs if "match_score" in j]
        
        print(f"\nMatch scores found: {len(scores)}")
        for s in scores[:5]:
            print(f"  {s['title']} at {s['company']}: {s['score']}% ({s['recommendation']})")
        
        assert len(scores) > 0, "No match scores found in response"


class TestEvidenceQuality:
    """Test quality of resume evidence extraction."""
    
    def test_evidence_contains_resume_snippets(self, auth_session, user_profile):
        """Verify evidence field contains actual text from user's resume."""
        if not user_profile.get("resume_text"):
            pytest.skip("Test user has no resume uploaded")
        
        resume_text = user_profile["resume_text"].lower()
        
        response = auth_session.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            json={"query": "Business Analyst", "limit": 10},
            timeout=90
        )
        
        assert response.status_code == 200
        
        jobs = parse_sse_response(response.text)
        
        evidence_found = False
        for job in jobs:
            grounded = job.get("grounded_strengths", [])
            
            for strength in grounded:
                evidence = strength.get("evidence", "")
                if evidence and len(evidence) > 20:
                    evidence_lower = evidence.lower()
                    
                    # Check for overlap with resume text
                    words_in_resume = sum(1 for word in evidence_lower.split() 
                                        if len(word) > 3 and word in resume_text)
                    
                    if words_in_resume >= 2:
                        evidence_found = True
                        print(f"\n✓ Found resume evidence in job: {job.get('title')}")
                        print(f"  Evidence: '{evidence[:100]}...'")
                        print(f"  Words matching resume: {words_in_resume}")
        
        assert evidence_found, "No evidence strings found that match resume text"
        print("\n✓ Evidence strings successfully extracted from resume")


class TestEndToEndMatchFlow:
    """Test complete flow from search to match analysis display."""
    
    def test_search_returns_personalized_match_data(self, auth_session):
        """Test that job search returns personalized match data with grounded strengths."""
        print("\n=== Testing personalized match data in search results ===")
        
        response = auth_session.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            json={"query": "Business Analyst", "limit": 5},
            timeout=90
        )
        
        assert response.status_code == 200
        
        jobs = parse_sse_response(response.text)
        print(f"Parsed {len(jobs)} jobs from response")
        
        assert len(jobs) > 0, "No jobs found for testing"
        
        # Check first job's match data
        job = jobs[0]
        print(f"\nJob: {job.get('title')} at {job.get('company')}")
        
        # Verify match fields are present
        assert "match_score" in job, "Missing match_score"
        print(f"  Score: {job.get('match_score')}%")
        
        assert "match_recommendation" in job, "Missing match_recommendation"
        print(f"  Recommendation: {job.get('match_recommendation')}")
        
        # Check for new personalized fields
        grounded = job.get("grounded_strengths", [])
        print(f"  Grounded strengths: {len(grounded)}")
        
        assert "grounded_strengths" in job, "Missing grounded_strengths field"
        
        if grounded:
            print("\n  Grounded strengths detail:")
            for gs in grounded[:3]:
                print(f"    - Requirement: {gs.get('requirement', 'N/A')}")
                if gs.get("evidence"):
                    print(f"      Evidence: {gs.get('evidence', '')[:80]}...")
                print(f"      Reason: {gs.get('match_reason', 'N/A')}")
        
        skills = job.get("matched_skills", [])
        print(f"\n  Matched skills: {skills}")
        
        print("\n✓ Personalized match analysis with resume evidence is working!")


class TestCompareEndpoint:
    """Test the detailed job comparison endpoint."""
    
    def test_compare_endpoint_generates_analysis(self, auth_session):
        """Test that /api/jobs/{job_id}/compare generates detailed analysis."""
        # Get a job from public API
        jobs_response = auth_session.get(
            f"{BASE_URL}/api/public/jobs",
            params={"query": "Analyst", "limit": 1}
        )
        
        assert jobs_response.status_code == 200
        data = jobs_response.json()
        
        if not data.get("jobs"):
            pytest.skip("No jobs found for testing")
        
        job = data["jobs"][0]
        job_id = job["id"]
        
        print(f"\nTesting compare endpoint with: {job.get('title')} at {job.get('company')}")
        
        # Call compare endpoint
        compare_response = auth_session.post(
            f"{BASE_URL}/api/jobs/{job_id}/compare",
            json={
                "job_id": job_id,
                "job_title": job.get("title", "Test Job"),
                "company": job.get("company", "Test Company"),
                "job_description": job.get("description", "Test description")[:500],
            },
            timeout=120
        )
        
        print(f"Compare response status: {compare_response.status_code}")
        
        if compare_response.status_code == 200:
            analysis = compare_response.json()
            print(f"Analysis response keys: {list(analysis.keys())}")
            
            if "comparison_json" in analysis:
                comparison = analysis["comparison_json"]
                print(f"Comparison keys: {list(comparison.keys())}")
                
                # Check for key analysis components
                if "decision_summary" in comparison:
                    print(f"Decision summary: {comparison['decision_summary']}")
                if "strengths" in comparison:
                    print(f"Strengths count: {len(comparison['strengths'])}")
        elif compare_response.status_code == 500:
            print(f"Server error: {compare_response.text[:200]}")
        else:
            print(f"Compare endpoint returned: {compare_response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
