#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import time
import threading

class JobMatchAPITester:
    def __init__(self, base_url="https://applypilot-9.preview.emergentagent.com"):
        self.base_url = base_url
        self.session_token = "test_session_1768797070346"  # From auth setup
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.session_token}'
        }

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Non-dict response'}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    'name': name,
                    'expected': expected_status,
                    'actual': response.status_code,
                    'response': response.text[:200]
                })

            return success, response.json() if success and response.text else {}

        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timed out after {timeout}s")
            self.failed_tests.append({'name': name, 'error': 'Timeout'})
            return False, {}
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.failed_tests.append({'name': name, 'error': str(e)})
            return False, {}

    def test_health_endpoints(self):
        """Test basic health endpoints"""
        print("\n" + "="*50)
        print("TESTING HEALTH ENDPOINTS")
        print("="*50)
        
        self.run_test("API Root", "GET", "", 200)
        self.run_test("Health Check", "GET", "health", 200)

    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print("\n" + "="*50)
        print("TESTING AUTH ENDPOINTS")
        print("="*50)
        
        self.run_test("Get Current User", "GET", "auth/me", 200)

    def test_profile_endpoints(self):
        """Test profile management endpoints"""
        print("\n" + "="*50)
        print("TESTING PROFILE ENDPOINTS")
        print("="*50)
        
        # Get profile
        success, profile = self.run_test("Get Profile", "GET", "profile", 200)
        
        if success:
            # Update profile
            update_data = {
                "skills": ["Python", "JavaScript", "React"],
                "experience_years": 3,
                "job_titles": ["Software Engineer", "Full Stack Developer"],
                "preferred_locations": ["New York", "Remote"],
                "salary_min": 80000,
                "salary_max": 120000,
                "job_type": ["full-time", "remote"]
            }
            self.run_test("Update Profile", "PUT", "profile", 200, update_data)

    def test_job_search_endpoints(self):
        """Test job search functionality"""
        print("\n" + "="*50)
        print("TESTING JOB SEARCH ENDPOINTS")
        print("="*50)
        
        # Test job search
        search_data = {
            "query": "software engineer",
            "location": "New York",
            "page": 1,
            "num_pages": 1,
            "employment_types": "FULLTIME"
        }
        success, jobs = self.run_test("Job Search", "POST", "jobs/search", 200, search_data, timeout=60)
        
        return success, jobs

    def test_greenhouse_streaming(self):
        """Test Greenhouse SSE streaming functionality"""
        print("\n" + "="*50)
        print("TESTING GREENHOUSE STREAMING")
        print("="*50)
        
        url = f"{self.base_url}/api/jobs/greenhouse/search"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.session_token}',
            'Accept': 'text/event-stream'
        }
        
        search_data = {
            "query": "engineer",
            "location": ""
        }
        
        self.tests_run += 1
        print(f"\n🔍 Testing Greenhouse SSE Streaming...")
        print(f"   URL: {url}")
        print(f"   Query: {search_data['query']}")
        
        start_time = time.time()
        jobs_received = 0
        completion_received = False
        first_job_time = None
        
        try:
            response = requests.post(url, json=search_data, headers=headers, stream=True, timeout=70)
            
            # Check response headers
            content_type = response.headers.get('content-type', '')
            if 'text/event-stream' not in content_type:
                print(f"❌ FAILED - Expected text/event-stream, got {content_type}")
                self.failed_tests.append({
                    'name': 'Greenhouse SSE Content Type',
                    'error': f'Wrong content type: {content_type}'
                })
                return False
            
            print(f"✅ Content-Type: {content_type}")
            
            # Process streaming response
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    data_str = line[6:]  # Remove 'data: ' prefix
                    try:
                        data = json.loads(data_str)
                        
                        if data.get('done'):
                            completion_received = True
                            total_jobs = data.get('total', 0)
                            elapsed = time.time() - start_time
                            print(f"✅ Completion message received: {total_jobs} jobs in {elapsed:.2f}s")
                            break
                        else:
                            jobs_received += 1
                            if first_job_time is None:
                                first_job_time = time.time() - start_time
                                print(f"✅ First job received after {first_job_time:.2f}s")
                            
                            # Validate job structure
                            required_fields = ['job_id', 'title', 'company', 'match_score']
                            missing_fields = [field for field in required_fields if field not in data]
                            if missing_fields:
                                print(f"⚠️  Job missing fields: {missing_fields}")
                            
                            if jobs_received <= 3:  # Show first few jobs
                                print(f"   Job {jobs_received}: {data.get('title', 'N/A')} at {data.get('company', 'N/A')} (Score: {data.get('match_score', 'N/A')})")
                    
                    except json.JSONDecodeError as e:
                        print(f"❌ Invalid JSON in stream: {data_str[:100]}")
                        continue
            
            elapsed_total = time.time() - start_time
            
            # Validate streaming performance
            success = True
            if not completion_received:
                print(f"❌ FAILED - No completion message received")
                success = False
            
            if elapsed_total > 60:
                print(f"❌ FAILED - Streaming took too long: {elapsed_total:.2f}s")
                success = False
            else:
                print(f"✅ Total streaming time: {elapsed_total:.2f}s")
            
            if first_job_time and first_job_time > 5:
                print(f"⚠️  First job took {first_job_time:.2f}s (should be < 5s)")
            
            if jobs_received < 5:
                print(f"⚠️  Only {jobs_received} jobs found (expected 10+)")
            else:
                print(f"✅ Received {jobs_received} jobs")
            
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Greenhouse streaming working correctly")
            else:
                self.failed_tests.append({
                    'name': 'Greenhouse SSE Streaming',
                    'error': 'Streaming validation failed'
                })
            
            return success
            
        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timed out after 70s")
            self.failed_tests.append({'name': 'Greenhouse SSE Streaming', 'error': 'Timeout'})
            return False
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.failed_tests.append({'name': 'Greenhouse SSE Streaming', 'error': str(e)})
            return False

    def test_greenhouse_companies(self):
        """Test Greenhouse companies endpoint"""
        print("\n🔍 Testing Greenhouse Companies...")
        success, companies = self.run_test("Get Greenhouse Companies", "GET", "jobs/greenhouse/companies", 200)
        
        if success and companies:
            company_list = companies.get('companies', [])
            print(f"   Found {len(company_list)} companies")
            if len(company_list) >= 10:
                print(f"✅ Good company coverage: {company_list[:5]}...")
            else:
                print(f"⚠️  Limited companies: {company_list}")
        
        return success

    def test_ai_endpoints(self):
        """Test AI-powered features"""
        print("\n" + "="*50)
        print("TESTING AI ENDPOINTS")
        print("="*50)
        
        # Test cover letter generation
        cover_data = {
            "job_title": "Software Engineer",
            "company": "Test Company",
            "job_description": "We are looking for a skilled software engineer to join our team."
        }
        self.run_test("Generate Cover Letter", "POST", "ai/cover-letter", 200, cover_data, timeout=60)
        
        # Test interview prep
        prep_data = {
            "job_title": "Software Engineer",
            "company": "Test Company", 
            "job_description": "We are looking for a skilled software engineer to join our team."
        }
        self.run_test("Generate Interview Prep", "POST", "ai/interview-prep", 200, prep_data, timeout=60)

    def test_application_endpoints(self):
        """Test application management"""
        print("\n" + "="*50)
        print("TESTING APPLICATION ENDPOINTS")
        print("="*50)
        
        # Create application
        app_data = {
            "job_id": "test_job_123",
            "job_title": "Software Engineer",
            "company": "Test Company",
            "location": "New York, NY",
            "job_description": "Test job description for software engineer position."
        }
        success, app = self.run_test("Create Application", "POST", "applications", 200, app_data)
        
        # Get applications
        self.run_test("Get Applications", "GET", "applications", 200)
        
        if success and app.get('application_id'):
            app_id = app['application_id']
            
            # Approve application
            self.run_test("Approve Application", "PUT", f"applications/{app_id}/approve", 200)
            
            # Try to reject (should still work)
            self.run_test("Reject Application", "PUT", f"applications/{app_id}/reject", 200)

    def test_dashboard_endpoints(self):
        """Test dashboard statistics"""
        print("\n" + "="*50)
        print("TESTING DASHBOARD ENDPOINTS")
        print("="*50)
        
        self.run_test("Get Dashboard Stats", "GET", "dashboard/stats", 200)

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting JobMatch AI API Tests")
        print(f"📍 Base URL: {self.base_url}")
        print(f"🔑 Session Token: {self.session_token[:20]}...")
        
        start_time = datetime.now()
        
        # Run test suites
        self.test_health_endpoints()
        self.test_auth_endpoints()
        self.test_profile_endpoints()
        self.test_job_search_endpoints()
        
        # Test Greenhouse streaming (high priority)
        self.test_greenhouse_companies()
        self.test_greenhouse_streaming()
        
        self.test_ai_endpoints()
        self.test_application_endpoints()
        self.test_dashboard_endpoints()
        
        # Print summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"✅ Tests passed: {self.tests_passed}/{self.tests_run}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        
        if self.failed_tests:
            print(f"\n❌ Failed tests ({len(self.failed_tests)}):")
            for test in self.failed_tests:
                error_msg = test.get('error', f"Expected {test.get('expected')}, got {test.get('actual')}")
                print(f"   • {test['name']}: {error_msg}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\n🎯 Success rate: {success_rate:.1f}%")
        
        return 0 if self.tests_passed == self.tests_run else 1

def main():
    tester = JobMatchAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())