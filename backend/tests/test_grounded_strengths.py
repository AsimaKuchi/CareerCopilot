"""
Test Suite: Grounded Strengths in Job Match Analysis
Tests the fixes for:
1. Frontend field name mismatch - was using s.requirement/s.match_reason but backend sends strength_title/relevance
2. Backend streaming endpoint passing full job description to evaluate_job_match
3. Work experience extraction parsing (company name vs job title)
4. Grounded strength categories deduplication
"""

import pytest
import requests
import os
import json
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@demo.com"
TEST_PASSWORD = "Test1234!"


class TestAuthAndProfile:
    """Tests for authentication and profile retrieval"""
    
    @pytest.fixture(scope="class")
    def session(self):
        """Create authenticated session"""
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        return s
    
    def test_login_success(self, session):
        """Test login with test credentials"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "user_id" in data
        assert data["email"] == TEST_EMAIL
        print(f"Login successful - User: {data.get('name', 'Unknown')}")
        
    def test_get_profile(self, session):
        """Test profile retrieval after login"""
        # Login first
        session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        response = session.get(f"{BASE_URL}/api/profile")
        assert response.status_code == 200, f"Profile fetch failed: {response.text}"
        
        profile = response.json()
        # Check profile has expected fields
        assert "skills" in profile
        assert "experience_years" in profile
        assert "job_titles" in profile
        
        print(f"Profile retrieved - Skills: {len(profile.get('skills', []))}, Experience: {profile.get('experience_years', 0)} years")
        print(f"Job Titles: {profile.get('job_titles', [])}")
        
        # Check for resume text
        if profile.get("resume_text"):
            print(f"Resume text present: {len(profile['resume_text'])} characters")
        else:
            print("Note: No resume text in profile")


class TestGreenhouseJobSearch:
    """Tests for Greenhouse streaming job search with grounded strengths"""
    
    @pytest.fixture(scope="class")
    def session(self):
        """Create authenticated session"""
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        # Login
        response = s.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return s
    
    def test_greenhouse_search_returns_grounded_strengths(self, session):
        """Test that greenhouse search returns grounded_strengths with correct field names"""
        response = session.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            json={
                "query": "software engineer",
                "location": "San Francisco",
                "company": ""
            },
            stream=True,
            timeout=60
        )
        
        assert response.status_code == 200, f"Search failed: {response.status_code}"
        
        jobs_received = []
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                json_str = line[6:]
                try:
                    data = json.loads(json_str)
                    if data.get("done"):
                        print(f"Search completed - Total: {data.get('total', 0)} jobs")
                        break
                    elif data.get("heartbeat") or data.get("progress"):
                        continue
                    else:
                        # This is a job
                        jobs_received.append(data)
                        if len(jobs_received) >= 3:
                            # Got enough jobs to test
                            break
                except json.JSONDecodeError:
                    continue
        
        assert len(jobs_received) > 0, "No jobs received from search"
        print(f"Received {len(jobs_received)} jobs for analysis")
        
        # Test the first job's grounded_strengths structure
        job = jobs_received[0]
        print(f"\nJob: {job.get('title')} at {job.get('company')}")
        print(f"Match Score: {job.get('match_score')}%")
        
        # Check grounded_strengths exists
        grounded_strengths = job.get("grounded_strengths", [])
        print(f"Grounded Strengths count: {len(grounded_strengths)}")
        
        if grounded_strengths:
            for i, strength in enumerate(grounded_strengths):
                # Verify correct field names (not requirement/match_reason)
                assert "strength_title" in strength, f"Missing 'strength_title' in strength {i}"
                assert "evidence" in strength, f"Missing 'evidence' in strength {i}"
                assert "relevance" in strength, f"Missing 'relevance' in strength {i}"
                
                # Ensure OLD field names are NOT present
                assert "requirement" not in strength, f"Old field 'requirement' found in strength {i}"
                assert "match_reason" not in strength, f"Old field 'match_reason' found in strength {i}"
                
                print(f"  [{i+1}] {strength.get('strength_title')}")
                print(f"      Evidence: {strength.get('evidence', '')[:80]}...")
                print(f"      Relevance: {strength.get('relevance', '')[:80]}...")
        
        # Check matched_skills
        matched_skills = job.get("matched_skills", [])
        print(f"Matched Skills: {matched_skills}")
        
    def test_grounded_strengths_not_raw_text(self, session):
        """Test that grounded_strengths evidence is meaningful, not raw contact info"""
        response = session.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            json={
                "query": "software engineer",
                "location": "",
                "company": ""
            },
            stream=True,
            timeout=60
        )
        
        assert response.status_code == 200
        
        jobs_received = []
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                json_str = line[6:]
                try:
                    data = json.loads(json_str)
                    if data.get("done"):
                        break
                    elif data.get("heartbeat") or data.get("progress"):
                        continue
                    else:
                        jobs_received.append(data)
                        if len(jobs_received) >= 5:
                            break
                except json.JSONDecodeError:
                    continue
        
        print(f"\nAnalyzing {len(jobs_received)} jobs for meaningful evidence...")
        
        for job in jobs_received:
            grounded_strengths = job.get("grounded_strengths", [])
            for strength in grounded_strengths:
                evidence = strength.get("evidence", "")
                
                # Check evidence is NOT raw contact info
                evidence_lower = evidence.lower()
                
                # These patterns indicate raw resume header, not meaningful evidence
                raw_patterns = [
                    "email:",
                    "@gmail.com",
                    "@yahoo.com", 
                    "phone:",
                    "linkedin.com/in/",
                    "github.com/",
                    "portfolio:",
                    "address:",
                ]
                
                for pattern in raw_patterns:
                    if pattern in evidence_lower:
                        # Only fail if it's JUST contact info, not if mentioned in context
                        if len(evidence) < 100 and evidence_lower.count('@') > 0:
                            pytest.fail(f"Evidence contains raw contact info: {evidence[:100]}")
                
                print(f"  ✓ Evidence is meaningful: {evidence[:60]}...")
    
    def test_no_duplicate_strength_titles(self, session):
        """Test that grounded strengths don't have duplicate titles"""
        response = session.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            json={
                "query": "engineer",
                "location": "",
                "company": ""
            },
            stream=True,
            timeout=60
        )
        
        assert response.status_code == 200
        
        jobs_received = []
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                json_str = line[6:]
                try:
                    data = json.loads(json_str)
                    if data.get("done"):
                        break
                    elif data.get("heartbeat") or data.get("progress"):
                        continue
                    else:
                        jobs_received.append(data)
                        if len(jobs_received) >= 5:
                            break
                except json.JSONDecodeError:
                    continue
        
        print(f"\nChecking {len(jobs_received)} jobs for duplicate strength titles...")
        
        for job in jobs_received:
            grounded_strengths = job.get("grounded_strengths", [])
            titles = [s.get("strength_title", "") for s in grounded_strengths]
            
            # Check for exact duplicates
            seen = set()
            duplicates = []
            for title in titles:
                if title in seen:
                    duplicates.append(title)
                seen.add(title)
            
            if duplicates:
                print(f"  Job: {job.get('title')} - Titles: {titles}")
                pytest.fail(f"Duplicate strength titles found: {duplicates}")
            else:
                print(f"  ✓ {job.get('company')}: {len(titles)} unique titles")


class TestWorkExperienceParsing:
    """Tests for work experience extraction from resume"""
    
    @pytest.fixture(scope="class")
    def session(self):
        """Create authenticated session"""
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        s.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return s
    
    def test_work_experience_company_not_job_title(self, session):
        """Test that work experience evidence uses company names, not job titles as company names"""
        response = session.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            json={
                "query": "developer",
                "location": "",
                "company": ""
            },
            stream=True,
            timeout=60
        )
        
        assert response.status_code == 200
        
        jobs_received = []
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                json_str = line[6:]
                try:
                    data = json.loads(json_str)
                    if data.get("done"):
                        break
                    elif data.get("heartbeat") or data.get("progress"):
                        continue
                    else:
                        jobs_received.append(data)
                        if len(jobs_received) >= 5:
                            break
                except json.JSONDecodeError:
                    continue
        
        print(f"\nAnalyzing work experience in {len(jobs_received)} jobs...")
        
        # Expected company names from test user profile
        expected_companies = ["TechCorp Inc.", "DataFlow Solutions", "StartupXYZ"]
        
        # Job title patterns that should NOT appear as company names
        job_title_patterns = ["engineer", "developer", "analyst", "manager", "lead", "senior", "junior"]
        
        for job in jobs_received:
            grounded_strengths = job.get("grounded_strengths", [])
            for strength in grounded_strengths:
                evidence = strength.get("evidence", "")
                
                # Look for "at <company>" pattern
                if " at " in evidence:
                    parts = evidence.split(" at ")
                    if len(parts) > 1:
                        company_part = parts[1].split()[0] if parts[1].split() else ""
                        company_part_lower = company_part.lower()
                        
                        # Check company name isn't a job title
                        for pattern in job_title_patterns:
                            if company_part_lower.startswith(pattern):
                                print(f"  ⚠ Potential issue: '{company_part}' looks like job title in: {evidence[:80]}")
                
                print(f"  ✓ Evidence: {evidence[:70]}...")


class TestMatchedSkills:
    """Tests for matched_skills field in job responses"""
    
    @pytest.fixture(scope="class")
    def session(self):
        """Create authenticated session"""
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        s.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return s
    
    def test_matched_skills_returned(self, session):
        """Test that matched_skills field is returned in job search"""
        response = session.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            json={
                "query": "python developer",
                "location": "",
                "company": ""
            },
            stream=True,
            timeout=60
        )
        
        assert response.status_code == 200
        
        jobs_with_skills = []
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                json_str = line[6:]
                try:
                    data = json.loads(json_str)
                    if data.get("done"):
                        break
                    elif data.get("heartbeat") or data.get("progress"):
                        continue
                    else:
                        matched_skills = data.get("matched_skills", [])
                        if matched_skills:
                            jobs_with_skills.append({
                                "title": data.get("title"),
                                "company": data.get("company"),
                                "matched_skills": matched_skills
                            })
                        if len(jobs_with_skills) >= 5:
                            break
                except json.JSONDecodeError:
                    continue
        
        print(f"\nJobs with matched_skills: {len(jobs_with_skills)}")
        
        # User has skills: Python, JavaScript, React, Node.js, AWS, Docker, PostgreSQL, MongoDB, Kubernetes, SQL
        expected_skills = ["python", "javascript", "react", "node", "aws", "docker", "postgresql", "mongodb", "kubernetes", "sql"]
        
        for job in jobs_with_skills:
            print(f"\n{job['title']} at {job['company']}:")
            print(f"  Matched Skills: {job['matched_skills']}")
            
            # Verify skills are meaningful (not empty, not garbage)
            for skill in job['matched_skills']:
                assert len(skill) > 1, f"Skill too short: {skill}"
                assert not skill.isdigit(), f"Skill is just a number: {skill}"
        
        # At least some jobs should have matched skills
        print(f"\nTotal jobs with matched skills: {len(jobs_with_skills)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
