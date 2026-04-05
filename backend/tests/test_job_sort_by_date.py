"""
Test job search sorting by posted_at date (descending - newest first)
Tests both streaming (/api/jobs/greenhouse/search) and non-streaming (/api/jobs/search) endpoints
"""
import pytest
import requests
import os
import json
from datetime import datetime
from dateutil import parser as date_parser

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@demo.com"
TEST_PASSWORD = "Test1234!"


class TestJobSortByDate:
    """Test that job search results are sorted by posted_at descending (newest first)"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        """Login and get authenticated session with CSRF token"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login to get session cookie and CSRF token
        login_response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        login_data = login_response.json()
        csrf_token = login_data.get("csrf_token")
        assert csrf_token, "No CSRF token in login response"
        
        # Add CSRF token to session headers for POST requests
        session.headers.update({"X-CSRF-Token": csrf_token})
        
        print(f"Login successful, CSRF token obtained: {csrf_token[:20]}...")
        return session
    
    def parse_date_safe(self, date_str):
        """Parse date string to datetime, return None if invalid"""
        if not date_str:
            return None
        try:
            return date_parser.parse(date_str)
        except (ValueError, TypeError):
            return None
    
    def test_streaming_search_sorted_by_date(self, auth_session):
        """
        Test POST /api/jobs/greenhouse/search streaming endpoint
        Verify jobs are returned sorted by posted_at descending (newest first)
        """
        # Make streaming search request
        response = auth_session.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            json={"query": "software engineer", "location": ""},
            stream=True,
            timeout=180  # Streaming can take a while
        )
        
        assert response.status_code == 200, f"Streaming search failed: {response.status_code}"
        assert "text/event-stream" in response.headers.get("Content-Type", ""), \
            f"Expected SSE content type, got: {response.headers.get('Content-Type')}"
        
        # Parse SSE stream and collect jobs
        jobs = []
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            
            data_str = line[6:]  # Remove "data: " prefix
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                continue
            
            # Skip heartbeat, progress, and done messages
            if data.get("heartbeat") or data.get("progress") or data.get("done"):
                continue
            
            # This is a job object
            if "posted_at" in data:
                jobs.append(data)
        
        print(f"Received {len(jobs)} jobs from streaming endpoint")
        assert len(jobs) > 0, "No jobs returned from streaming search"
        
        # Verify sort order - jobs should be sorted by posted_at descending
        sort_violations = 0
        prev_date = None
        
        for i, job in enumerate(jobs):
            posted_at = job.get("posted_at", "")
            current_date = self.parse_date_safe(posted_at)
            
            if prev_date and current_date:
                if current_date > prev_date:
                    sort_violations += 1
                    print(f"Sort violation at index {i}: {current_date} > {prev_date}")
            
            prev_date = current_date
        
        print(f"Sort violations: {sort_violations} out of {len(jobs)} jobs")
        
        # Show first 5 and last 5 dates for verification
        print("\nFirst 5 job dates:")
        for job in jobs[:5]:
            print(f"  - {job.get('posted_at', 'N/A')} | {job.get('title', 'N/A')[:50]}")
        
        print("\nLast 5 job dates:")
        for job in jobs[-5:]:
            print(f"  - {job.get('posted_at', 'N/A')} | {job.get('title', 'N/A')[:50]}")
        
        assert sort_violations == 0, f"Jobs not sorted by date descending: {sort_violations} violations"
    
    def test_non_streaming_search_sorted_by_date(self, auth_session):
        """
        Test POST /api/jobs/search non-streaming endpoint
        Verify jobs are returned sorted by posted_at descending (newest first)
        """
        # Make non-streaming search request
        response = auth_session.post(
            f"{BASE_URL}/api/jobs/search",
            json={"query": "software engineer", "location": "remote"},
            timeout=120
        )
        
        assert response.status_code == 200, f"Non-streaming search failed: {response.status_code} - {response.text}"
        
        data = response.json()
        jobs = data.get("jobs", [])
        total = data.get("total", 0)
        
        print(f"Received {len(jobs)} jobs (total: {total}) from non-streaming endpoint")
        
        if len(jobs) == 0:
            pytest.skip("No jobs returned from non-streaming search - may need different query")
        
        # Verify sort order - jobs should be sorted by posted_at descending
        sort_violations = 0
        prev_date = None
        
        for i, job in enumerate(jobs):
            posted_at = job.get("posted_at", "")
            current_date = self.parse_date_safe(posted_at)
            
            if prev_date and current_date:
                if current_date > prev_date:
                    sort_violations += 1
                    print(f"Sort violation at index {i}: {current_date} > {prev_date}")
            
            prev_date = current_date
        
        print(f"Sort violations: {sort_violations} out of {len(jobs)} jobs")
        
        # Show first 5 and last 5 dates for verification
        if len(jobs) >= 5:
            print("\nFirst 5 job dates:")
            for job in jobs[:5]:
                print(f"  - {job.get('posted_at', 'N/A')} | {job.get('title', 'N/A')[:50]}")
            
            print("\nLast 5 job dates:")
            for job in jobs[-5:]:
                print(f"  - {job.get('posted_at', 'N/A')} | {job.get('title', 'N/A')[:50]}")
        
        assert sort_violations == 0, f"Jobs not sorted by date descending: {sort_violations} violations"
    
    def test_streaming_search_date_format_consistency(self, auth_session):
        """
        Verify that posted_at dates in streaming response are in consistent ISO format
        """
        response = auth_session.post(
            f"{BASE_URL}/api/jobs/greenhouse/search",
            json={"query": "data analyst", "location": ""},
            stream=True,
            timeout=180
        )
        
        assert response.status_code == 200
        
        jobs = []
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            
            data_str = line[6:]
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                continue
            
            if data.get("heartbeat") or data.get("progress") or data.get("done"):
                continue
            
            if "posted_at" in data:
                jobs.append(data)
        
        if len(jobs) == 0:
            pytest.skip("No jobs returned")
        
        # Check date format consistency
        valid_dates = 0
        empty_dates = 0
        invalid_dates = 0
        
        for job in jobs:
            posted_at = job.get("posted_at", "")
            if not posted_at:
                empty_dates += 1
            else:
                parsed = self.parse_date_safe(posted_at)
                if parsed:
                    valid_dates += 1
                else:
                    invalid_dates += 1
                    print(f"Invalid date format: {posted_at}")
        
        print(f"\nDate format analysis:")
        print(f"  Valid dates: {valid_dates}")
        print(f"  Empty dates: {empty_dates}")
        print(f"  Invalid dates: {invalid_dates}")
        
        # All non-empty dates should be parseable
        assert invalid_dates == 0, f"Found {invalid_dates} jobs with invalid date formats"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
