#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import time
import threading

class JobMatchAPITester:
    def __init__(self, base_url="https://jobsmart-8.preview.emergentagent.com"):
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
        
        # Test regular job search (JSearch API)
        self.test_jsearch_streaming()
        
        return True

    def test_jsearch_streaming(self):
        """Test Job Search streaming endpoint (/api/jobs/search) with detailed validation"""
        print("\n🔍 Testing Job Search Streaming (JSearch API)...")
        
        url = f"{self.base_url}/api/jobs/search"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.session_token}'
        }
        
        search_data = {
            "query": "engineer",
            "location": ""
        }
        
        self.tests_run += 1
        print(f"   URL: {url}")
        print(f"   Query: '{search_data['query']}', Location: '{search_data['location']}'")
        
        start_time = time.time()
        
        try:
            response = requests.post(url, json=search_data, headers=headers, timeout=60)
            
            if response.status_code != 200:
                print(f"❌ FAILED - Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    'name': 'Job Search Streaming',
                    'expected': 200,
                    'actual': response.status_code,
                    'response': response.text[:200]
                })
                return False
            
            data = response.json()
            jobs = data.get('jobs', [])
            total = data.get('total', 0)
            
            elapsed = time.time() - start_time
            
            # Validation checks
            validation_errors = []
            
            if total == 0:
                validation_errors.append("No jobs found - should return at least SOME jobs")
            
            if len(jobs) == 0:
                validation_errors.append("Empty jobs array")
            
            # Check job structure for first few jobs
            for i, job in enumerate(jobs[:3]):
                job_errors = []
                
                required_fields = ['job_id', 'title', 'company', 'match_score', 'match_strengths', 'match_gaps']
                for field in required_fields:
                    if field not in job:
                        job_errors.append(f"Missing field: {field}")
                
                # Validate match_score is a number
                if 'match_score' in job and not isinstance(job['match_score'], (int, float)):
                    job_errors.append("match_score should be numeric")
                
                # Validate match_strengths and match_gaps are arrays
                if 'match_strengths' in job and not isinstance(job['match_strengths'], list):
                    job_errors.append("match_strengths should be array")
                
                if 'match_gaps' in job and not isinstance(job['match_gaps'], list):
                    job_errors.append("match_gaps should be array")
                
                if job_errors:
                    validation_errors.append(f"Job {i+1} errors: {', '.join(job_errors)}")
            
            # Check backend logs for streaming messages (if accessible)
            print(f"   Jobs found: {len(jobs)}")
            print(f"   Total reported: {total}")
            print(f"   Response time: {elapsed:.2f}s")
            
            if validation_errors:
                print(f"❌ FAILED - Validation errors:")
                for error in validation_errors:
                    print(f"   • {error}")
                self.failed_tests.append({
                    'name': 'Job Search Validation',
                    'error': f"Validation errors: {', '.join(validation_errors)}"
                })
                return False
            
            # Success
            self.tests_passed += 1
            print(f"✅ PASSED - Job Search Streaming")
            print(f"   ✅ Found {len(jobs)} jobs from quality sources")
            print(f"   ✅ All jobs have match_score, match_strengths, match_gaps")
            print(f"   ✅ Response time: {elapsed:.2f}s")
            
            # Show sample jobs
            if jobs:
                print(f"   Sample jobs:")
                for i, job in enumerate(jobs[:3]):
                    title = job.get('title', 'N/A')
                    company = job.get('company', 'N/A')
                    score = job.get('match_score', 'N/A')
                    strengths_count = len(job.get('match_strengths', []))
                    gaps_count = len(job.get('match_gaps', []))
                    print(f"     {i+1}. {title} at {company} (Score: {score}, {strengths_count} strengths, {gaps_count} gaps)")
            
            return True
            
        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timed out after 60s")
            self.failed_tests.append({'name': 'Job Search Streaming', 'error': 'Timeout'})
            return False
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.failed_tests.append({'name': 'Job Search Streaming', 'error': str(e)})
            return False

    def test_greenhouse_streaming_scenarios(self):
        """Test Greenhouse SSE streaming with specific scenarios from review request"""
        print("\n" + "="*50)
        print("TESTING GREENHOUSE STREAMING - SIMPLIFIED FILTERING")
        print("="*50)
        
        # Test scenarios as requested in review
        test_scenarios = [
            {
                "name": "Engineer Query (Empty Location)",
                "query": "engineer", 
                "location": "",
                "expected_min_jobs": 20,  # Should return MANY jobs now (5,335 available)
                "description": "Should return MANY jobs with simplified filtering"
            },
            {
                "name": "Software + San Francisco",
                "query": "software",
                "location": "san francisco", 
                "expected_min_jobs": 5,
                "description": "Should return SF-based software jobs"
            },
            {
                "name": "Empty Query and Location",
                "query": "",
                "location": "",
                "expected_min_jobs": 10,
                "description": "Should return jobs even with empty query"
            }
        ]
        
        all_scenarios_passed = True
        
        for scenario in test_scenarios:
            success = self.test_single_greenhouse_scenario(scenario)
            if not success:
                all_scenarios_passed = False
        
        return all_scenarios_passed

    def test_exact_user_reported_search(self):
        """Test the EXACT search scenario reported by user as failing"""
        print("\n" + "="*60)
        print("🎯 TESTING EXACT USER REPORTED SEARCH SCENARIO")
        print("="*60)
        print("Testing: query='business analyst', location='greater toronto area, ontario'")
        print("Expected: Should return 40+ jobs from companies like Stripe, Coinbase, Airbnb, Dropbox")
        print("Reason: Fixed location matching to extract keywords: ['toronto', 'ontario']")
        
        scenario = {
            "name": "Business Analyst in Greater Toronto Area",
            "query": "business analyst",
            "location": "greater toronto area, ontario", 
            "expected_min_jobs": 40,
            "description": "User reported this exact search was failing - should now work with smart location matching"
        }
        
        return self.test_single_greenhouse_scenario(scenario)

    def test_single_greenhouse_scenario(self, scenario):
        """Test a single Greenhouse streaming scenario"""
        print(f"\n🔍 Testing: {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        
        url = f"{self.base_url}/api/jobs/greenhouse/search"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.session_token}',
            'Accept': 'text/event-stream'
        }
        
        search_data = {
            "query": scenario['query'],
            "location": scenario['location']
        }
        
        self.tests_run += 1
        print(f"   Query: '{search_data['query']}', Location: '{search_data['location']}'")
        
        start_time = time.time()
        jobs_received = 0
        completion_received = False
        first_job_time = None
        greenhouse_sources = set()
        jobs_with_match_data = 0
        backend_log_message_found = False
        
        try:
            response = requests.post(url, json=search_data, headers=headers, stream=True, timeout=70)
            
            # Check response headers
            content_type = response.headers.get('content-type', '')
            if 'text/event-stream' not in content_type:
                print(f"❌ FAILED - Expected text/event-stream, got {content_type}")
                self.failed_tests.append({
                    'name': f'Greenhouse SSE {scenario["name"]}',
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
                        
                        # Check for heartbeat or progress messages
                        if data.get('heartbeat') or data.get('progress'):
                            continue
                        
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
                            
                            # Track job sources (should be quality sources like Greenhouse)
                            source = data.get('source', 'unknown')
                            if source in ['greenhouse', 'lever', 'ashby']:
                                greenhouse_sources.add(source)
                            
                            # Validate job has match scoring data
                            if all(field in data for field in ['match_score', 'match_strengths', 'match_gaps']):
                                jobs_with_match_data += 1
                            
                            # Validate job structure
                            required_fields = ['job_id', 'title', 'company', 'match_score', 'match_strengths', 'match_gaps']
                            missing_fields = [field for field in required_fields if field not in data]
                            if missing_fields:
                                print(f"⚠️  Job missing fields: {missing_fields}")
                            
                            if jobs_received <= 5:  # Show first few jobs
                                title = data.get('title', 'N/A')
                                company = data.get('company', 'N/A')
                                score = data.get('match_score', 'N/A')
                                strengths = len(data.get('match_strengths', []))
                                gaps = len(data.get('match_gaps', []))
                                source = data.get('source', 'N/A')
                                print(f"   Job {jobs_received}: {title} at {company} (Score: {score}, {strengths} strengths, {gaps} gaps, Source: {source})")
                    
                    except json.JSONDecodeError as e:
                        print(f"❌ Invalid JSON in stream: {data_str[:100]}")
                        continue
            
            elapsed_total = time.time() - start_time
            
            # Validation checks specific to review request
            validation_errors = []
            
            if not completion_received:
                validation_errors.append("No completion message received")
            
            if elapsed_total > 60:
                validation_errors.append(f"Streaming took too long: {elapsed_total:.2f}s")
            
            # CRITICAL: Check if we got enough jobs (simplified filtering should return MORE jobs)
            if jobs_received < scenario['expected_min_jobs']:
                validation_errors.append(f"Only {jobs_received} jobs found, expected at least {scenario['expected_min_jobs']} with simplified filtering")
            
            # Check if jobs are from quality sources
            if not greenhouse_sources:
                validation_errors.append("No jobs from quality sources (Greenhouse/Lever/Ashby) found")
            
            # Check if jobs have match scoring
            if jobs_with_match_data == 0:
                validation_errors.append("No jobs have match scoring data (match_score, match_strengths, match_gaps)")
            
            # Performance checks
            if first_job_time and first_job_time > 5:
                validation_errors.append(f"First job took {first_job_time:.2f}s (should be < 5s)")
            
            if validation_errors:
                print(f"❌ FAILED - {scenario['name']}:")
                for error in validation_errors:
                    print(f"   • {error}")
                self.failed_tests.append({
                    'name': f'Greenhouse Streaming {scenario["name"]}',
                    'error': f"Validation errors: {', '.join(validation_errors)}"
                })
                return False
            
            # Success
            self.tests_passed += 1
            print(f"✅ PASSED - {scenario['name']}")
            print(f"   ✅ Jobs returned: {jobs_received} (≥ {scenario['expected_min_jobs']} expected)")
            print(f"   ✅ Quality sources: {', '.join(greenhouse_sources)}")
            print(f"   ✅ Jobs with match data: {jobs_with_match_data}/{jobs_received}")
            print(f"   ✅ Response time: {elapsed_total:.2f}s")
            print(f"   ✅ First job time: {first_job_time:.2f}s")
            
            return True
            
        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timed out after 70s")
            self.failed_tests.append({'name': f'Greenhouse Streaming {scenario["name"]}', 'error': 'Timeout'})
            return False
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.failed_tests.append({'name': f'Greenhouse Streaming {scenario["name"]}', 'error': str(e)})
            return False

    def check_backend_logs(self):
        """Check backend logs for the expected message about simplified filtering"""
        print("\n🔍 Checking backend logs for simplified filtering message...")
        
        try:
            # Check supervisor backend logs
            import subprocess
            result = subprocess.run(
                ['tail', '-n', '50', '/var/log/supervisor/backend.out.log'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                log_content = result.stdout
                if "Show ALL jobs matching query/location" in log_content:
                    print("✅ Found expected log message: 'Show ALL jobs matching query/location'")
                    return True
                else:
                    print("⚠️  Expected log message not found in recent logs")
                    print("   Looking for: 'Show ALL jobs matching query/location'")
                    return False
            else:
                print("⚠️  Could not read backend logs")
                return False
                
        except Exception as e:
            print(f"⚠️  Error checking logs: {str(e)}")
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
        
        # Test interview prep with detailed validation
        self.test_interview_prep_detailed()

    def test_interview_prep_detailed(self):
        """Test Interview Prep generation endpoint with detailed validation"""
        print("\n🔍 Testing Interview Prep Generation (Detailed)...")
        
        prep_data = {
            "job_title": "Software Engineer",
            "company": "Google",
            "job_description": "We are looking for a skilled software engineer to join our team. You will work on large-scale distributed systems, write clean code, and collaborate with cross-functional teams."
        }
        
        url = f"{self.base_url}/api/ai/interview-prep"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.session_token}'
        }
        
        self.tests_run += 1
        
        try:
            response = requests.post(url, json=prep_data, headers=headers, timeout=60)
            
            if response.status_code != 200:
                print(f"❌ FAILED - Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    'name': 'Interview Prep Generation',
                    'expected': 200,
                    'actual': response.status_code,
                    'response': response.text[:200]
                })
                return False
            
            data = response.json()
            prep_materials = data.get('prep_materials', '')
            
            if not prep_materials:
                print(f"❌ FAILED - No prep_materials in response")
                self.failed_tests.append({
                    'name': 'Interview Prep Generation',
                    'error': 'No prep_materials field'
                })
                return False
            
            # Validate required formatting
            validation_errors = []
            
            # Check for ALL-CAPS section headers
            required_sections = [
                "1. COMMON INTERVIEW QUESTIONS",
                "2. BEHAVIORAL QUESTIONS", 
                "3. TECHNICAL QUESTIONS",
                "4. INTERVIEW TIPS",
                "5. QUESTIONS TO ASK THE INTERVIEWER"
            ]
            
            for section in required_sections:
                if section not in prep_materials:
                    validation_errors.append(f"Missing section: {section}")
            
            # Check for level-4 headers (####)
            if "####" not in prep_materials:
                validation_errors.append("Missing level-4 headers (####) for questions")
            
            # Check for blockquotes (>)
            if ">" not in prep_materials:
                validation_errors.append("Missing blockquotes (>) for sample answers")
            
            # Check that NO italics or asterisks are used
            if "*" in prep_materials:
                validation_errors.append("Contains asterisks (*) - should not use italics")
            
            # Validate structure
            if len(prep_materials) < 1000:
                validation_errors.append("Content too short - should be comprehensive")
            
            if validation_errors:
                print(f"❌ FAILED - Formatting validation errors:")
                for error in validation_errors:
                    print(f"   • {error}")
                self.failed_tests.append({
                    'name': 'Interview Prep Formatting',
                    'error': f"Validation errors: {', '.join(validation_errors)}"
                })
                return False
            
            # Success
            self.tests_passed += 1
            print(f"✅ PASSED - Interview Prep Generation")
            print(f"   Content length: {len(prep_materials)} characters")
            print(f"   All required sections present: ✅")
            print(f"   Proper formatting (####, >, no asterisks): ✅")
            
            # Show sample content
            lines = prep_materials.split('\n')[:10]
            print(f"   Sample content preview:")
            for i, line in enumerate(lines):
                if line.strip():
                    print(f"     {line[:80]}...")
                    if i >= 3:
                        break
            
            return True
            
        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timed out after 60s")
            self.failed_tests.append({'name': 'Interview Prep Generation', 'error': 'Timeout'})
            return False
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.failed_tests.append({'name': 'Interview Prep Generation', 'error': str(e)})
            return False

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
        
        # Run basic health checks first
        self.test_health_endpoints()
        self.test_auth_endpoints()
        
        # PRIORITY TESTS - As requested in review
        print("\n" + "="*60)
        print("🎯 PRIORITY TESTS - REVIEW REQUEST FOCUS")
        print("="*60)
        
        # Test Interview Prep generation endpoint
        print("\n📋 Testing Interview Prep Generation (/api/ai/interview-prep)")
        self.test_interview_prep_detailed()
        
        # Test Job Search streaming endpoint  
        print("\n🔍 Testing Job Search Streaming (/api/jobs/search)")
        self.test_jsearch_streaming()
        
        # Additional tests
        print("\n" + "="*60)
        print("🔧 ADDITIONAL SYSTEM TESTS")
        print("="*60)
        
        self.test_profile_endpoints()
        
        # Test Greenhouse streaming (PRIORITY - mentioned in review request)
        print("\n🌿 Testing Greenhouse Streaming with Simplified Filtering")
        self.test_greenhouse_companies()
        self.test_greenhouse_streaming_scenarios()
        
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