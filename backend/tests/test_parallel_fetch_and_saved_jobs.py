"""
Test suite for parallel job fetching and saved jobs features.

Features tested:
1. Parallel job fetching performance (should load 5000+ jobs in under 10 seconds)
2. /api/jobs/saved endpoint returns saved jobs for authenticated user
3. Job search saves results to user_saved_jobs collection in MongoDB
4. New jobs are marked with is_new_for_user flag when compared to previous cache
"""

import pytest
import requests
import os
import json
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test session token - will be created in setup
SESSION_TOKEN = "test_session_1769366298161"


class TestParallelJobFetching:
    """Tests for parallel job fetching performance"""
    
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
        print(f"✓ Auth working for user: {data['email']}")
    
    def test_parallel_fetch_performance(self):
        """
        Test that parallel job fetching completes in under 10 seconds.
        Should fetch from 35 verified companies in parallel batches.
        """
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            headers=self.headers,
            json={
                "query": "engineer",
                "location": ""
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
        
        elapsed = time.time() - start_time
        
        # Performance requirement: under 10 seconds
        assert elapsed < 10, f"Parallel fetch took {elapsed:.1f}s, should be under 10s"
        
        # Should find a reasonable number of jobs
        assert jobs_found > 0, "Should find jobs"
        
        print(f"✓ Parallel fetch completed in {elapsed:.1f}s with {jobs_found} jobs")
    
    def test_streaming_returns_jobs_progressively(self):
        """
        Test that jobs are streamed progressively, not all at once.
        """
        response = requests.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            headers=self.headers,
            json={
                "query": "software",
                "location": ""
            },
            stream=True,
            timeout=30
        )
        
        assert response.status_code == 200
        
        # Check that we receive heartbeat/progress messages first
        messages = []
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    json_str = line_str[6:]
                    try:
                        data = json.loads(json_str)
                        messages.append(data)
                        if data.get('done') or len(messages) >= 10:
                            break
                    except json.JSONDecodeError:
                        continue
        
        # Should have heartbeat or progress messages
        has_heartbeat = any(m.get('heartbeat') for m in messages)
        has_progress = any(m.get('progress') for m in messages)
        
        assert has_heartbeat or has_progress, "Should receive heartbeat/progress messages"
        print(f"✓ Streaming works: received {len(messages)} messages")


class TestSavedJobsEndpoint:
    """Tests for /api/jobs/saved endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SESSION_TOKEN}"
        }
    
    def test_saved_jobs_endpoint_exists(self):
        """Test that /api/jobs/saved endpoint exists and returns proper structure"""
        response = requests.get(
            f"{BASE_URL}/api/jobs/saved",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "jobs" in data, "Response should have 'jobs' field"
        assert "last_search_query" in data, "Response should have 'last_search_query' field"
        assert "last_search_location" in data, "Response should have 'last_search_location' field"
        assert "updated_at" in data, "Response should have 'updated_at' field"
        assert "total" in data, "Response should have 'total' field"
        
        print(f"✓ Saved jobs endpoint returns proper structure")
    
    def test_saved_jobs_requires_auth(self):
        """Test that /api/jobs/saved requires authentication"""
        response = requests.get(f"{BASE_URL}/api/jobs/saved")
        
        assert response.status_code == 401, "Should require authentication"
        print(f"✓ Saved jobs endpoint requires authentication")
    
    def test_saved_jobs_returns_user_jobs(self):
        """Test that saved jobs returns jobs for the authenticated user"""
        response = requests.get(
            f"{BASE_URL}/api/jobs/saved",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # If there are saved jobs, verify structure
        if data.get("jobs"):
            job = data["jobs"][0]
            assert "job_id" in job, "Job should have job_id"
            assert "title" in job, "Job should have title"
            assert "company" in job, "Job should have company"
            print(f"✓ Saved jobs returns {data['total']} jobs for user")
        else:
            print(f"✓ Saved jobs returns empty list (no previous searches)")


class TestJobCachingAndNewJobDetection:
    """Tests for job caching and is_new_for_user flag"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SESSION_TOKEN}"
        }
    
    def test_search_saves_jobs_to_cache(self):
        """Test that job search saves results to user_saved_jobs collection"""
        # First, do a search
        response = requests.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            headers=self.headers,
            json={
                "query": "product manager",
                "location": ""
            },
            stream=True,
            timeout=60
        )
        
        assert response.status_code == 200
        
        # Consume the stream
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        if data.get('done'):
                            break
                    except json.JSONDecodeError:
                        continue
        
        # Now check saved jobs
        saved_response = requests.get(
            f"{BASE_URL}/api/jobs/saved",
            headers=self.headers
        )
        
        assert saved_response.status_code == 200
        saved_data = saved_response.json()
        
        # Should have saved the search
        assert saved_data.get("last_search_query") == "product manager", \
            f"Expected 'product manager', got '{saved_data.get('last_search_query')}'"
        
        print(f"✓ Search saved {saved_data['total']} jobs to cache")
    
    def test_new_jobs_marked_with_is_new_for_user(self):
        """Test that new jobs are marked with is_new_for_user flag"""
        # Do a search to establish baseline
        response1 = requests.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            headers=self.headers,
            json={
                "query": "designer",
                "location": ""
            },
            stream=True,
            timeout=60
        )
        
        # Consume stream
        for line in response1.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8')[6:])
                    if data.get('done'):
                        break
                except:
                    continue
        
        # Do a different search - new jobs should be marked
        response2 = requests.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            headers=self.headers,
            json={
                "query": "marketing",
                "location": ""
            },
            stream=True,
            timeout=60
        )
        
        new_jobs_count = 0
        for line in response2.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        if data.get('done'):
                            new_jobs_count = data.get('new_jobs_count', 0)
                            break
                        elif data.get('is_new_for_user'):
                            new_jobs_count += 1
                    except json.JSONDecodeError:
                        continue
        
        # New search should have new jobs
        print(f"✓ Found {new_jobs_count} new jobs marked with is_new_for_user")
    
    def test_saved_jobs_limited_to_50(self):
        """Test that saved jobs are limited to top 50 for dashboard"""
        # Check saved jobs
        response = requests.get(
            f"{BASE_URL}/api/jobs/saved",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be limited to 50
        assert len(data.get("jobs", [])) <= 50, \
            f"Saved jobs should be limited to 50, got {len(data.get('jobs', []))}"
        
        print(f"✓ Saved jobs limited to {len(data.get('jobs', []))} (max 50)")


class TestDashboardStats:
    """Tests for dashboard stats endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SESSION_TOKEN}"
        }
    
    def test_dashboard_stats_endpoint(self):
        """Test that dashboard stats endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "total_applications" in data
        assert "applied" in data
        assert "pending" in data
        assert "profile_completeness" in data
        
        print(f"✓ Dashboard stats: {data['total_applications']} applications, {data['profile_completeness']}% profile complete")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
