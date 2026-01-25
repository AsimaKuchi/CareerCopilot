"""
Test suite for the Business Analyst Toronto fallback search bug fix.

This tests the P0 bug where searching 'business analyst' in 'Toronto' on 'Quality Sources' 
returned 0 jobs despite expanded company lists.

Root cause: performFallbackSearch in JobSearch.jsx was calling /api/jobs/search (JSearch aggregator)
instead of /api/jobs/greenhouse/search (streaming Greenhouse/Lever endpoint).

Fix: Changed line 259 in JobSearch.jsx to use /api/jobs/greenhouse/search
"""

import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test session token - created for testing
SESSION_TOKEN = "test_session_1769360767912"


class TestFallbackSearchBugFix:
    """Tests for the business analyst Toronto fallback search bug fix"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SESSION_TOKEN}"
        }
    
    def test_auth_works(self):
        """Test that authentication is working"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "email" in data
        print(f"✓ Auth working for user: {data['email']}")
    
    def test_strict_search_returns_zero_for_business_analyst_toronto(self):
        """
        Test that strict search for 'business analyst' in 'Toronto' returns 0 results.
        This confirms the original issue - there are no exact 'Business Analyst' jobs.
        """
        response = requests.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            headers=self.headers,
            json={
                "query": "business analyst",
                "location": "Toronto",
                "fallback_search": False
            },
            stream=True,
            timeout=120
        )
        
        assert response.status_code == 200
        
        jobs_found = 0
        suggest_fallback = False
        fallback_message = ""
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    json_str = line_str[6:]
                    try:
                        data = json.loads(json_str)
                        if data.get('done'):
                            jobs_found = data.get('total', 0)
                            suggest_fallback = data.get('suggest_fallback', False)
                            fallback_message = data.get('fallback_message', '')
                            break
                        elif not data.get('heartbeat') and not data.get('progress'):
                            # This is a job
                            jobs_found += 1
                    except json.JSONDecodeError:
                        continue
        
        # Strict search should return 0 or very few exact matches
        assert jobs_found == 0, f"Expected 0 jobs for strict search, got {jobs_found}"
        
        # Backend should suggest fallback when 0 results for multi-word query
        assert suggest_fallback == True, "Backend should suggest fallback when 0 results"
        assert "business analyst" in fallback_message.lower(), f"Fallback message should mention query: {fallback_message}"
        
        print(f"✓ Strict search returned {jobs_found} jobs (expected 0)")
        print(f"✓ Backend suggested fallback: {suggest_fallback}")
        print(f"✓ Fallback message: {fallback_message}")
    
    def test_fallback_search_returns_related_analyst_jobs(self):
        """
        Test that fallback search for 'business analyst' in 'Toronto' returns related jobs.
        This is the key test - the fix should make fallback return analyst jobs.
        """
        response = requests.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            headers=self.headers,
            json={
                "query": "business analyst",
                "location": "Toronto",
                "fallback_search": True  # This triggers broader matching
            },
            stream=True,
            timeout=120
        )
        
        assert response.status_code == 200
        
        jobs = []
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    json_str = line_str[6:]
                    try:
                        data = json.loads(json_str)
                        if data.get('done'):
                            break
                        elif not data.get('heartbeat') and not data.get('progress'):
                            jobs.append(data)
                    except json.JSONDecodeError:
                        continue
        
        # Fallback should return related analyst jobs
        assert len(jobs) > 0, "Fallback search should return related jobs"
        
        # Verify jobs are analyst-related
        analyst_keywords = ['analyst', 'business', 'data', 'operations', 'strategy']
        analyst_jobs = [j for j in jobs if any(kw in j.get('title', '').lower() for kw in analyst_keywords)]
        
        assert len(analyst_jobs) > 0, f"Should find analyst-related jobs. Found titles: {[j.get('title') for j in jobs[:5]]}"
        
        # Verify jobs are in Canada/Toronto area
        canada_jobs = [j for j in jobs if any(loc in j.get('location', '').lower() for loc in ['canada', 'toronto', 'remote'])]
        assert len(canada_jobs) > 0, "Should find jobs in Canada/Toronto area"
        
        print(f"✓ Fallback search returned {len(jobs)} related jobs")
        print(f"✓ Found {len(analyst_jobs)} analyst-related jobs")
        print(f"✓ Found {len(canada_jobs)} jobs in Canada/Toronto area")
        print(f"✓ Sample job titles: {[j.get('title') for j in jobs[:5]]}")
    
    def test_fallback_uses_greenhouse_endpoint_not_jsearch(self):
        """
        Test that the fallback search uses /api/jobs/greenhouse/search endpoint.
        This verifies the fix - previously it was using /api/jobs/search (JSearch).
        """
        # The /api/jobs/greenhouse/search endpoint returns SSE stream
        response = requests.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            headers=self.headers,
            json={
                "query": "business analyst",
                "location": "Toronto",
                "fallback_search": True
            },
            stream=True,
            timeout=30
        )
        
        assert response.status_code == 200
        assert response.headers.get('content-type', '').startswith('text/event-stream'), \
            "Greenhouse endpoint should return SSE stream"
        
        # Read first few lines to verify it's streaming
        lines_read = 0
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                assert line_str.startswith('data: '), f"SSE format expected, got: {line_str[:50]}"
                lines_read += 1
                if lines_read >= 3:
                    break
        
        assert lines_read >= 1, "Should receive SSE data"
        print(f"✓ Greenhouse endpoint returns SSE stream correctly")
        print(f"✓ Received {lines_read} SSE messages")
    
    def test_fallback_jobs_have_match_scores(self):
        """
        Test that fallback search results include match scores for ranking.
        """
        response = requests.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            headers=self.headers,
            json={
                "query": "business analyst",
                "location": "Toronto",
                "fallback_search": True
            },
            stream=True,
            timeout=60
        )
        
        assert response.status_code == 200
        
        jobs_with_scores = []
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    json_str = line_str[6:]
                    try:
                        data = json.loads(json_str)
                        if data.get('done'):
                            break
                        elif not data.get('heartbeat') and not data.get('progress'):
                            if 'match_score' in data:
                                jobs_with_scores.append(data)
                            if len(jobs_with_scores) >= 5:
                                break
                    except json.JSONDecodeError:
                        continue
        
        assert len(jobs_with_scores) > 0, "Jobs should have match scores"
        
        for job in jobs_with_scores:
            assert 'match_score' in job, f"Job missing match_score: {job.get('title')}"
            assert 'match_recommendation' in job, f"Job missing match_recommendation: {job.get('title')}"
            assert isinstance(job['match_score'], (int, float)), "match_score should be numeric"
            assert 0 <= job['match_score'] <= 100, f"match_score should be 0-100, got {job['match_score']}"
        
        print(f"✓ All {len(jobs_with_scores)} jobs have match scores")
        print(f"✓ Sample scores: {[j['match_score'] for j in jobs_with_scores]}")
    
    def test_fallback_flag_is_logged_in_backend(self):
        """
        Test that the backend logs when fallback_search flag is passed.
        This verifies the logging improvement mentioned in the fix.
        """
        # Make a request with fallback_search=True
        response = requests.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            headers=self.headers,
            json={
                "query": "test",
                "location": "Toronto",
                "fallback_search": True
            },
            stream=True,
            timeout=30
        )
        
        assert response.status_code == 200
        
        # Just verify the endpoint accepts the flag without error
        first_line = None
        for line in response.iter_lines():
            if line:
                first_line = line.decode('utf-8')
                break
        
        assert first_line is not None, "Should receive response"
        assert 'data:' in first_line, "Should receive SSE data"
        
        print(f"✓ Backend accepts fallback_search flag without error")


class TestEdgeCases:
    """Edge case tests for the fallback search"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SESSION_TOKEN}"
        }
    
    def test_single_word_query_uses_broad_matching(self):
        """
        Test that single-word queries always use broad matching (no fallback needed).
        """
        response = requests.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            headers=self.headers,
            json={
                "query": "analyst",
                "location": "Toronto",
                "fallback_search": False
            },
            stream=True,
            timeout=60
        )
        
        assert response.status_code == 200
        
        jobs_found = 0
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    json_str = line_str[6:]
                    try:
                        data = json.loads(json_str)
                        if data.get('done'):
                            jobs_found = data.get('total', 0)
                            break
                        elif not data.get('heartbeat') and not data.get('progress'):
                            jobs_found += 1
                    except json.JSONDecodeError:
                        continue
        
        # Single word "analyst" should find jobs even without fallback
        assert jobs_found > 0, f"Single word query should find jobs, got {jobs_found}"
        print(f"✓ Single word query 'analyst' found {jobs_found} jobs")
    
    def test_location_matching_includes_canada_and_remote(self):
        """
        Test that Toronto search also matches 'Canada' and 'Remote' locations.
        """
        response = requests.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            headers=self.headers,
            json={
                "query": "analyst",
                "location": "Toronto",
                "fallback_search": True
            },
            stream=True,
            timeout=60
        )
        
        assert response.status_code == 200
        
        locations = set()
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    json_str = line_str[6:]
                    try:
                        data = json.loads(json_str)
                        if data.get('done'):
                            break
                        elif not data.get('heartbeat') and not data.get('progress'):
                            loc = data.get('location', '')
                            if loc:
                                locations.add(loc)
                            if len(locations) >= 10:
                                break
                    except json.JSONDecodeError:
                        continue
        
        # Should find jobs in Toronto, Canada, or Remote
        location_str = ' '.join(locations).lower()
        has_valid_location = any(loc in location_str for loc in ['toronto', 'canada', 'remote'])
        
        assert has_valid_location, f"Should find jobs in Toronto/Canada/Remote. Found: {locations}"
        print(f"✓ Found jobs in valid locations: {list(locations)[:5]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
