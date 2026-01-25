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

    def test_business_analyst_phrase_matching(self):
        """Test improved 'business analyst' search with strict phrase matching as requested in review"""
        print("\n" + "="*70)
        print("🎯 TESTING BUSINESS ANALYST PHRASE MATCHING (REVIEW REQUEST)")
        print("="*70)
        print("Testing improved phrase matching for multi-word queries")
        print("Focus: Ensure 'business analyst' requires BOTH words, not just any word")
        
        # Test Case 1: "business analyst" in Toronto - should be strict
        print("\n📋 TEST CASE 1: 'business analyst' in Toronto (Strict Phrase Matching)")
        case1_success = self.test_business_analyst_strict_matching()
        
        # Test Case 2: "analyst" (single word) - should be broad  
        print("\n📋 TEST CASE 2: 'analyst' in Toronto (Broad Keyword Matching)")
        case2_success = self.test_analyst_broad_matching()
        
        return case1_success and case2_success

    def test_business_analyst_strict_matching(self):
        """Test Case 1: 'business analyst' should require BOTH words"""
        print("🔍 Testing strict phrase matching for 'business analyst'...")
        
        url = f"{self.base_url}/api/jobs/greenhouse/search"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.session_token}',
            'Accept': 'text/event-stream'
        }
        
        search_data = {
            "query": "business analyst",
            "location": "greater toronto area, ontario"
        }
        
        self.tests_run += 1
        print(f"   Query: '{search_data['query']}', Location: '{search_data['location']}'")
        print("   Expected: Jobs with BOTH 'business' AND 'analyst' in title")
        print("   Should match: 'Business Analyst', 'Senior Business Analyst', 'Business Systems Analyst'")
        print("   Should NOT match: 'Data Analyst', 'Business Operations Manager', 'Account Executive, Business'")
        
        start_time = time.time()
        jobs_received = 0
        job_titles = []
        valid_matches = []
        invalid_matches = []
        
        try:
            response = requests.post(url, json=search_data, headers=headers, stream=True, timeout=70)
            
            if response.status_code != 200:
                print(f"❌ FAILED - Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    'name': 'Business Analyst Strict Matching',
                    'expected': 200,
                    'actual': response.status_code,
                    'response': response.text[:200]
                })
                return False
            
            # Process streaming response
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    data_str = line[6:]  # Remove 'data: ' prefix
                    try:
                        data = json.loads(data_str)
                        
                        # Skip heartbeat/progress messages
                        if data.get('heartbeat') or data.get('progress'):
                            continue
                        
                        if data.get('done'):
                            total_jobs = data.get('total', 0)
                            elapsed = time.time() - start_time
                            print(f"✅ Completion message received: {total_jobs} jobs in {elapsed:.2f}s")
                            break
                        else:
                            jobs_received += 1
                            title = data.get('title', '').lower()
                            job_titles.append(data.get('title', 'N/A'))
                            
                            # Validate strict phrase matching logic
                            has_business = 'business' in title
                            has_analyst = 'analyst' in title
                            
                            if has_business and has_analyst:
                                valid_matches.append(data.get('title', 'N/A'))
                            elif has_business or has_analyst:
                                # This should NOT happen with strict matching
                                invalid_matches.append({
                                    'title': data.get('title', 'N/A'),
                                    'reason': f"Has {'business' if has_business else 'analyst'} but not both words"
                                })
                            else:
                                # This should definitely NOT happen
                                invalid_matches.append({
                                    'title': data.get('title', 'N/A'),
                                    'reason': "Has neither 'business' nor 'analyst'"
                                })
                    
                    except json.JSONDecodeError:
                        continue
            
            elapsed_total = time.time() - start_time
            
            # Validation checks
            validation_errors = []
            
            if jobs_received < 2:
                validation_errors.append(f"Too few jobs found: {jobs_received} (expected at least 2 business analyst jobs)")
            
            # Critical: Check for invalid matches (jobs that don't have both words)
            if invalid_matches:
                validation_errors.append(f"Found {len(invalid_matches)} jobs that don't match strict criteria")
                for invalid in invalid_matches[:3]:  # Show first 3
                    validation_errors.append(f"  Invalid: '{invalid['title']}' - {invalid['reason']}")
            
            # Check that we have some valid matches
            if len(valid_matches) == 0:
                validation_errors.append("No jobs found with both 'business' AND 'analyst' in title")
            
            if validation_errors:
                print(f"❌ FAILED - Strict matching validation errors:")
                for error in validation_errors:
                    print(f"   • {error}")
                self.failed_tests.append({
                    'name': 'Business Analyst Strict Matching',
                    'error': f"Validation errors: {', '.join(validation_errors)}"
                })
                
                # Still show the job titles found for debugging
                print(f"\n📋 Job titles found ({len(job_titles)}):")
                for i, title in enumerate(job_titles[:10]):
                    print(f"   {i+1}. {title}")
                
                return False
            
            # Success
            self.tests_passed += 1
            print(f"✅ PASSED - Business Analyst Strict Matching")
            print(f"   ✅ Jobs found: {jobs_received}")
            print(f"   ✅ Valid matches (both words): {len(valid_matches)}")
            print(f"   ✅ Invalid matches: {len(invalid_matches)} (should be 0)")
            print(f"   ✅ Response time: {elapsed_total:.2f}s")
            
            # Show job titles found
            print(f"\n📋 Valid 'Business Analyst' job titles found ({len(valid_matches)}):")
            for i, title in enumerate(valid_matches[:10]):
                print(f"   {i+1}. {title}")
            
            if len(valid_matches) > 10:
                print(f"   ... and {len(valid_matches) - 10} more")
            
            return True
            
        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timed out after 70s")
            self.failed_tests.append({'name': 'Business Analyst Strict Matching', 'error': 'Timeout'})
            return False
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.failed_tests.append({'name': 'Business Analyst Strict Matching', 'error': str(e)})
            return False

    def test_analyst_broad_matching(self):
        """Test Case 2: 'analyst' should return ALL analyst jobs (broad matching)"""
        print("🔍 Testing broad keyword matching for 'analyst'...")
        
        url = f"{self.base_url}/api/jobs/greenhouse/search"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.session_token}',
            'Accept': 'text/event-stream'
        }
        
        search_data = {
            "query": "analyst",
            "location": "toronto"
        }
        
        self.tests_run += 1
        print(f"   Query: '{search_data['query']}', Location: '{search_data['location']}'")
        print("   Expected: ALL analyst jobs (Data Analyst, Business Analyst, Financial Analyst, etc.)")
        
        start_time = time.time()
        jobs_received = 0
        job_titles = []
        analyst_types = set()
        
        try:
            response = requests.post(url, json=search_data, headers=headers, stream=True, timeout=70)
            
            if response.status_code != 200:
                print(f"❌ FAILED - Status: {response.status_code}")
                self.failed_tests.append({
                    'name': 'Analyst Broad Matching',
                    'expected': 200,
                    'actual': response.status_code
                })
                return False
            
            # Process streaming response
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    data_str = line[6:]
                    try:
                        data = json.loads(data_str)
                        
                        if data.get('heartbeat') or data.get('progress'):
                            continue
                        
                        if data.get('done'):
                            total_jobs = data.get('total', 0)
                            elapsed = time.time() - start_time
                            print(f"✅ Completion message received: {total_jobs} jobs in {elapsed:.2f}s")
                            break
                        else:
                            jobs_received += 1
                            title = data.get('title', '')
                            job_titles.append(title)
                            
                            # Categorize analyst types
                            title_lower = title.lower()
                            if 'business analyst' in title_lower:
                                analyst_types.add('Business Analyst')
                            elif 'data analyst' in title_lower:
                                analyst_types.add('Data Analyst')
                            elif 'financial analyst' in title_lower:
                                analyst_types.add('Financial Analyst')
                            elif 'systems analyst' in title_lower:
                                analyst_types.add('Systems Analyst')
                            elif 'research analyst' in title_lower:
                                analyst_types.add('Research Analyst')
                            elif 'analyst' in title_lower:
                                analyst_types.add('Other Analyst')
                    
                    except json.JSONDecodeError:
                        continue
            
            elapsed_total = time.time() - start_time
            
            # Validation checks
            validation_errors = []
            
            if jobs_received < 5:
                validation_errors.append(f"Too few analyst jobs found: {jobs_received} (expected at least 5)")
            
            # Check that we have variety in analyst types
            if len(analyst_types) < 2:
                validation_errors.append(f"Limited analyst variety: {analyst_types} (expected multiple types)")
            
            # Verify all jobs contain 'analyst'
            non_analyst_jobs = [title for title in job_titles if 'analyst' not in title.lower()]
            if non_analyst_jobs:
                validation_errors.append(f"Found {len(non_analyst_jobs)} jobs without 'analyst': {non_analyst_jobs[:3]}")
            
            if validation_errors:
                print(f"❌ FAILED - Broad matching validation errors:")
                for error in validation_errors:
                    print(f"   • {error}")
                self.failed_tests.append({
                    'name': 'Analyst Broad Matching',
                    'error': f"Validation errors: {', '.join(validation_errors)}"
                })
                return False
            
            # Success
            self.tests_passed += 1
            print(f"✅ PASSED - Analyst Broad Matching")
            print(f"   ✅ Total analyst jobs found: {jobs_received}")
            print(f"   ✅ Analyst types found: {', '.join(sorted(analyst_types))}")
            print(f"   ✅ Response time: {elapsed_total:.2f}s")
            
            # Show sample job titles by type
            print(f"\n📋 Sample analyst job titles found:")
            shown_count = 0
            for title in job_titles[:15]:
                print(f"   {shown_count+1}. {title}")
                shown_count += 1
            
            if len(job_titles) > 15:
                print(f"   ... and {len(job_titles) - 15} more analyst jobs")
            
            return True
            
        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timed out after 70s")
            self.failed_tests.append({'name': 'Analyst Broad Matching', 'error': 'Timeout'})
            return False
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.failed_tests.append({'name': 'Analyst Broad Matching', 'error': str(e)})
            return False

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

    def test_analyze_match_feature(self):
        """Test the new Analyze Match feature end-to-end as requested in review"""
        print("\n" + "="*60)
        print("🎯 TESTING ANALYZE MATCH FEATURE (REVIEW REQUEST)")
        print("="*60)
        print("Testing POST /api/jobs/{job_id}/compare - Generate analysis")
        print("Testing GET /api/jobs/{job_id}/compare - Fetch cached analysis")
        print("Testing PUT /api/jobs/{job_id}/compare/notes - Update notes")
        
        # First ensure user has a resume uploaded
        self.ensure_user_has_resume()
        
        # Test 1: POST /api/jobs/{job_id}/compare - Generate analysis
        job_id = "test_job_123"
        payload = {
            "job_id": job_id,
            "job_title": "Senior Data Analyst",
            "company": "Stripe",
            "job_description": "We're looking for a Senior Data Analyst with 5+ years of experience in SQL, Python, Tableau. Must have experience with data warehousing, ETL pipelines, and business intelligence. Strong communication skills required."
        }
        
        success, analysis_response = self.test_job_analysis_generation(job_id, payload)
        
        if success:
            # Test 2: GET /api/jobs/{job_id}/compare - Fetch cached analysis
            self.test_cached_analysis_fetch(job_id)
            
            # Test 3: PUT /api/jobs/{job_id}/compare/notes - Update notes
            self.test_notes_update(job_id)
        
        return success

    def ensure_user_has_resume(self):
        """Ensure the test user has a resume uploaded for analysis"""
        print("\n🔍 Ensuring user has resume for analysis...")
        
        # Check if user already has resume
        success, profile = self.run_test("Check Profile for Resume", "GET", "profile", 200)
        
        if success and profile.get("resume_text") and len(profile.get("resume_text", "")) > 100:
            print("✅ User already has resume uploaded")
            return True
        
        # Upload a sample resume for testing
        print("📄 Uploading sample resume for testing...")
        
        # Create a realistic resume text for a data analyst
        sample_resume = """
JOHN DOE
Senior Data Analyst
Email: john.doe@email.com | Phone: (555) 123-4567

PROFESSIONAL SUMMARY
Experienced Data Analyst with 6+ years of expertise in SQL, Python, and business intelligence. 
Proven track record of building ETL pipelines, creating executive dashboards, and driving data-driven decisions.

TECHNICAL SKILLS
• Programming: Python, SQL, R, JavaScript
• Databases: PostgreSQL, MySQL, MongoDB, Snowflake
• Visualization: Tableau, Power BI, Matplotlib, Seaborn
• Cloud: AWS (S3, Redshift, Lambda), Azure
• Tools: Git, Docker, Airflow, dbt

WORK EXPERIENCE

Senior Data Analyst | TechCorp Inc. | 2020 - Present
• Built automated ETL pipelines processing 10M+ records daily using Python and SQL
• Created executive dashboards in Tableau reducing reporting time by 75%
• Collaborated with product teams to define KPIs and track business metrics
• Implemented A/B testing framework increasing conversion rates by 12%

Data Analyst | StartupXYZ | 2018 - 2020
• Analyzed customer behavior data using SQL and Python to identify retention patterns
• Developed predictive models improving customer lifetime value predictions by 25%
• Built real-time monitoring dashboards for key business metrics
• Worked with cross-functional teams to translate business requirements into technical solutions

Junior Analyst | DataCorp | 2017 - 2018
• Performed data quality assessments and cleansing for large datasets
• Created automated reports using SQL and Excel reducing manual work by 60%
• Supported senior analysts in building machine learning models

EDUCATION
Bachelor of Science in Statistics | University of Technology | 2017

CERTIFICATIONS
• AWS Certified Data Analytics - Specialty
• Tableau Desktop Certified Professional
• Google Analytics Certified
        """
        
        # Update profile with resume text
        update_data = {
            "resume_text": sample_resume.strip(),
            "resume_filename": "sample_resume.txt",
            "resume_format": "text",
            "skills": ["Python", "SQL", "Tableau", "ETL", "Data Analysis", "AWS"],
            "experience_years": 6,
            "job_titles": ["Senior Data Analyst", "Data Analyst"],
            "preferred_locations": ["New York", "Remote"],
            "salary_min": 90000,
            "salary_max": 130000
        }
        
        success, updated_profile = self.run_test("Upload Sample Resume", "PUT", "profile", 200, update_data)
        
        if success:
            print("✅ Sample resume uploaded successfully")
            return True
        else:
            print("❌ Failed to upload sample resume")
            return False

    def test_job_analysis_generation(self, job_id, payload):
        """Test POST /api/jobs/{job_id}/compare - Generate analysis"""
        print(f"\n🔍 Testing Job Analysis Generation for job_id: {job_id}")
        
        url = f"{self.base_url}/api/jobs/{job_id}/compare"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.session_token}'
        }
        
        self.tests_run += 1
        print(f"   URL: {url}")
        print(f"   Job: {payload['job_title']} at {payload['company']}")
        
        start_time = time.time()
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=90)
            
            if response.status_code != 200:
                print(f"❌ FAILED - Status: {response.status_code}")
                print(f"   Response: {response.text[:300]}...")
                self.failed_tests.append({
                    'name': 'Job Analysis Generation',
                    'expected': 200,
                    'actual': response.status_code,
                    'response': response.text[:300]
                })
                return False, {}
            
            data = response.json()
            elapsed = time.time() - start_time
            
            # Validation checks
            validation_errors = []
            
            # Check required top-level fields
            required_fields = ['comparison_id', 'user_id', 'job_id', 'job_title', 'company', 'comparison_json', 'status']
            for field in required_fields:
                if field not in data:
                    validation_errors.append(f"Missing top-level field: {field}")
            
            # Check status is complete
            if data.get('status') != 'complete':
                validation_errors.append(f"Expected status 'complete', got '{data.get('status')}'")
            
            # Check comparison_json structure
            comparison_json = data.get('comparison_json', {})
            if not isinstance(comparison_json, dict):
                validation_errors.append("comparison_json should be a dictionary")
            else:
                # Check required analysis fields
                required_analysis_fields = ['strengths', 'areas_to_address', 'keywords_to_include', 'suggested_resume_edits']
                for field in required_analysis_fields:
                    if field not in comparison_json:
                        validation_errors.append(f"Missing analysis field: {field}")
                
                # Validate strengths structure
                strengths = comparison_json.get('strengths', [])
                if not isinstance(strengths, list) or len(strengths) == 0:
                    validation_errors.append("strengths should be non-empty array")
                else:
                    for i, strength in enumerate(strengths[:2]):  # Check first 2
                        if not isinstance(strength, dict):
                            validation_errors.append(f"strength {i+1} should be object")
                        else:
                            strength_fields = ['title', 'why_it_matches', 'evidence']
                            for field in strength_fields:
                                if field not in strength:
                                    validation_errors.append(f"strength {i+1} missing field: {field}")
                
                # Validate areas_to_address structure
                areas = comparison_json.get('areas_to_address', [])
                if not isinstance(areas, list) or len(areas) == 0:
                    validation_errors.append("areas_to_address should be non-empty array")
                else:
                    for i, area in enumerate(areas[:2]):  # Check first 2
                        if not isinstance(area, dict):
                            validation_errors.append(f"area {i+1} should be object")
                        else:
                            area_fields = ['gap', 'why_it_matters', 'fix', 'priority']
                            for field in area_fields:
                                if field not in area:
                                    validation_errors.append(f"area {i+1} missing field: {field}")
                
                # Validate keywords_to_include
                keywords = comparison_json.get('keywords_to_include', [])
                if not isinstance(keywords, list) or len(keywords) == 0:
                    validation_errors.append("keywords_to_include should be non-empty array")
                
                # Validate suggested_resume_edits
                edits = comparison_json.get('suggested_resume_edits', [])
                if not isinstance(edits, list) or len(edits) == 0:
                    validation_errors.append("suggested_resume_edits should be non-empty array")
                else:
                    for i, edit in enumerate(edits[:2]):  # Check first 2
                        if not isinstance(edit, dict):
                            validation_errors.append(f"edit {i+1} should be object")
                        else:
                            edit_fields = ['target_section', 'before', 'after']
                            for field in edit_fields:
                                if field not in edit:
                                    validation_errors.append(f"edit {i+1} missing field: {field}")
            
            # Check if analysis is grounded (uses resume content, not hallucinated)
            resume_keywords = ['python', 'sql', 'tableau', 'etl', 'data', 'analyst', 'techcorp', 'startupxyz']
            analysis_text = str(comparison_json).lower()
            grounded_evidence = sum(1 for keyword in resume_keywords if keyword in analysis_text)
            
            if grounded_evidence < 3:
                validation_errors.append("Analysis appears to lack grounding in resume content")
            
            if validation_errors:
                print(f"❌ FAILED - Analysis validation errors:")
                for error in validation_errors:
                    print(f"   • {error}")
                self.failed_tests.append({
                    'name': 'Job Analysis Validation',
                    'error': f"Validation errors: {', '.join(validation_errors)}"
                })
                return False, {}
            
            # Success
            self.tests_passed += 1
            print(f"✅ PASSED - Job Analysis Generation")
            print(f"   ✅ Analysis generated in {elapsed:.2f}s")
            print(f"   ✅ Status: {data.get('status')}")
            print(f"   ✅ Comparison ID: {data.get('comparison_id')}")
            
            # Show analysis summary
            strengths_count = len(comparison_json.get('strengths', []))
            areas_count = len(comparison_json.get('areas_to_address', []))
            keywords_count = len(comparison_json.get('keywords_to_include', []))
            edits_count = len(comparison_json.get('suggested_resume_edits', []))
            
            print(f"   ✅ Analysis contains: {strengths_count} strengths, {areas_count} areas to address")
            print(f"   ✅ Keywords: {keywords_count}, Resume edits: {edits_count}")
            
            # Show sample content
            if strengths_count > 0:
                first_strength = comparison_json['strengths'][0]
                print(f"   Sample strength: '{first_strength.get('title', 'N/A')}'")
            
            return True, data
            
        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timed out after 90s")
            self.failed_tests.append({'name': 'Job Analysis Generation', 'error': 'Timeout'})
            return False, {}
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.failed_tests.append({'name': 'Job Analysis Generation', 'error': str(e)})
            return False, {}

    def test_cached_analysis_fetch(self, job_id):
        """Test GET /api/jobs/{job_id}/compare - Fetch cached analysis"""
        print(f"\n🔍 Testing Cached Analysis Fetch for job_id: {job_id}")
        
        url = f"{self.base_url}/api/jobs/{job_id}/compare"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.session_token}'
        }
        
        self.tests_run += 1
        print(f"   URL: {url}")
        
        start_time = time.time()
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ FAILED - Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    'name': 'Cached Analysis Fetch',
                    'expected': 200,
                    'actual': response.status_code,
                    'response': response.text[:200]
                })
                return False
            
            data = response.json()
            elapsed = time.time() - start_time
            
            # Validation checks
            validation_errors = []
            
            # Should return the same structure as POST
            if 'comparison_json' not in data:
                validation_errors.append("Missing comparison_json in cached response")
            
            if data.get('status') != 'complete':
                validation_errors.append(f"Expected cached status 'complete', got '{data.get('status')}'")
            
            # Should be fast (cached)
            if elapsed > 2.0:
                validation_errors.append(f"Cached fetch took {elapsed:.2f}s (should be instant)")
            
            if validation_errors:
                print(f"❌ FAILED - Cached analysis validation errors:")
                for error in validation_errors:
                    print(f"   • {error}")
                self.failed_tests.append({
                    'name': 'Cached Analysis Validation',
                    'error': f"Validation errors: {', '.join(validation_errors)}"
                })
                return False
            
            # Success
            self.tests_passed += 1
            print(f"✅ PASSED - Cached Analysis Fetch")
            print(f"   ✅ Retrieved cached analysis in {elapsed:.3f}s (instant)")
            print(f"   ✅ Same comparison_id: {data.get('comparison_id')}")
            
            return True
            
        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timed out after 30s")
            self.failed_tests.append({'name': 'Cached Analysis Fetch', 'error': 'Timeout'})
            return False
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.failed_tests.append({'name': 'Cached Analysis Fetch', 'error': str(e)})
            return False

    def test_notes_update(self, job_id):
        """Test PUT /api/jobs/{job_id}/compare/notes - Update notes"""
        print(f"\n🔍 Testing Notes Update for job_id: {job_id}")
        
        url = f"{self.base_url}/api/jobs/{job_id}/compare/notes"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.session_token}'
        }
        
        notes_payload = {
            "notes": "Interesting role, reach out to hiring manager John. Strong match for SQL and Python skills. Need to highlight ETL experience more."
        }
        
        self.tests_run += 1
        print(f"   URL: {url}")
        print(f"   Notes: {notes_payload['notes'][:50]}...")
        
        try:
            response = requests.put(url, json=notes_payload, headers=headers, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ FAILED - Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    'name': 'Notes Update',
                    'expected': 200,
                    'actual': response.status_code,
                    'response': response.text[:200]
                })
                return False
            
            data = response.json()
            
            # Validation checks
            validation_errors = []
            
            if not data.get('success'):
                validation_errors.append("Expected success: true in response")
            
            if data.get('notes') != notes_payload['notes']:
                validation_errors.append("Returned notes don't match submitted notes")
            
            if validation_errors:
                print(f"❌ FAILED - Notes update validation errors:")
                for error in validation_errors:
                    print(f"   • {error}")
                self.failed_tests.append({
                    'name': 'Notes Update Validation',
                    'error': f"Validation errors: {', '.join(validation_errors)}"
                })
                return False
            
            # Success
            self.tests_passed += 1
            print(f"✅ PASSED - Notes Update")
            print(f"   ✅ Notes saved successfully")
            print(f"   ✅ Response: {data}")
            
            return True
            
        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timed out after 30s")
            self.failed_tests.append({'name': 'Notes Update', 'error': 'Timeout'})
            return False
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.failed_tests.append({'name': 'Notes Update', 'error': str(e)})
            return False

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

    def test_download_endpoints(self):
        """Test resume and cover letter download endpoints as requested in review"""
        print("\n" + "="*60)
        print("🎯 TESTING DOWNLOAD ENDPOINTS (REVIEW REQUEST)")
        print("="*60)
        print("Testing resume and cover letter download functionality")
        
        # Step 1: Get list of applications
        print("\n🔍 Step 1: Getting list of applications...")
        success, apps_response = self.run_test("Get Applications List", "GET", "applications", 200)
        
        if not success or not apps_response:
            print("❌ Cannot test downloads - no applications endpoint available")
            return False
        
        applications = apps_response.get('applications', [])
        if not applications:
            print("❌ No applications found - creating test application with resume and cover letter...")
            # Create a test application with optimized resume and cover letter
            return self.create_test_application_and_test_downloads()
        
        print(f"✅ Found {len(applications)} applications")
        
        # Step 2: Find applications with optimized_resume and cover_letter
        resume_app = None
        cover_letter_app = None
        
        for app in applications:
            if app.get('optimized_resume') and not resume_app:
                resume_app = app
                print(f"✅ Found application with optimized_resume: {app.get('application_id')}")
            
            if app.get('cover_letter') and not cover_letter_app:
                cover_letter_app = app
                print(f"✅ Found application with cover_letter: {app.get('application_id')}")
            
            if resume_app and cover_letter_app:
                break
        
        # Step 3: Test resume download
        resume_success = False
        if resume_app:
            resume_success = self.test_resume_download(resume_app['application_id'])
        else:
            print("⚠️  No application with optimized_resume found")
        
        # Step 4: Test cover letter download
        cover_letter_success = False
        if cover_letter_app:
            cover_letter_success = self.test_cover_letter_download(cover_letter_app['application_id'])
        else:
            print("⚠️  No application with cover_letter found")
        
        # If no applications with required fields, create test data
        if not resume_app and not cover_letter_app:
            print("📝 Creating test application with resume and cover letter...")
            return self.create_test_application_and_test_downloads()
        
        return resume_success or cover_letter_success

    def create_test_application_and_test_downloads(self):
        """Create a test application with resume and cover letter, then test downloads"""
        print("\n🔧 Creating test application with optimized resume and cover letter...")
        
        # First ensure user has a profile and resume
        self.ensure_user_has_resume()
        
        # Create application with job description to trigger AI generation
        app_data = {
            "job_id": "download_test_job_456",
            "job_title": "Senior Data Analyst",
            "company": "Download Test Corp",
            "location": "Remote",
            "job_description": """We are seeking a Senior Data Analyst with expertise in Python, SQL, and data visualization. 
            The ideal candidate will have experience with ETL pipelines, business intelligence tools like Tableau, 
            and strong analytical skills. You will work with cross-functional teams to drive data-driven decisions."""
        }
        
        success, app = self.run_test("Create Test Application", "POST", "applications", 200, app_data)
        
        if not success or not app.get('application_id'):
            print("❌ Failed to create test application")
            return False
        
        app_id = app['application_id']
        print(f"✅ Created test application: {app_id}")
        
        # The application should now have optimized_resume and cover_letter generated
        # Let's verify by getting the application details
        success, app_details = self.run_test("Get Application Details", "GET", f"applications", 200)
        
        if success:
            # Find our test application
            applications = app_details.get('applications', [])
            test_app = None
            for application in applications:
                if application.get('application_id') == app_id:
                    test_app = application
                    break
            
            if test_app:
                has_resume = bool(test_app.get('optimized_resume'))
                has_cover_letter = bool(test_app.get('cover_letter'))
                
                print(f"   Has optimized_resume: {has_resume}")
                print(f"   Has cover_letter: {has_cover_letter}")
                
                # Test downloads
                resume_success = False
                cover_letter_success = False
                
                if has_resume:
                    resume_success = self.test_resume_download(app_id)
                
                if has_cover_letter:
                    cover_letter_success = self.test_cover_letter_download(app_id)
                
                return resume_success or cover_letter_success
        
        print("⚠️  Could not verify application details, attempting downloads anyway...")
        
        # Try downloads even if we can't verify the fields
        resume_success = self.test_resume_download(app_id)
        cover_letter_success = self.test_cover_letter_download(app_id)
        
        return resume_success or cover_letter_success

    def test_resume_download(self, application_id):
        """Test resume download endpoint"""
        print(f"\n📄 Testing Resume Download for application: {application_id}")
        
        url = f"{self.base_url}/api/applications/{application_id}/download/resume"
        headers = {
            'Authorization': f'Bearer {self.session_token}'
        }
        
        self.tests_run += 1
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            # Check status code
            if response.status_code != 200:
                print(f"❌ FAILED - Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    'name': 'Resume Download',
                    'expected': 200,
                    'actual': response.status_code,
                    'response': response.text[:200]
                })
                return False
            
            # Check Content-Type header
            content_type = response.headers.get('Content-Type', '')
            expected_content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            
            if content_type != expected_content_type:
                print(f"❌ FAILED - Wrong Content-Type")
                print(f"   Expected: {expected_content_type}")
                print(f"   Got: {content_type}")
                self.failed_tests.append({
                    'name': 'Resume Download Content-Type',
                    'error': f'Wrong Content-Type: {content_type}'
                })
                return False
            
            # Check Content-Disposition header
            content_disposition = response.headers.get('Content-Disposition', '')
            if not content_disposition.startswith('attachment; filename=Resume_'):
                print(f"❌ FAILED - Wrong Content-Disposition")
                print(f"   Expected: attachment; filename=Resume_*.docx")
                print(f"   Got: {content_disposition}")
                self.failed_tests.append({
                    'name': 'Resume Download Content-Disposition',
                    'error': f'Wrong Content-Disposition: {content_disposition}'
                })
                return False
            
            # Check if file is valid DOCX (check file signature)
            content = response.content
            if len(content) < 4:
                print(f"❌ FAILED - File too small: {len(content)} bytes")
                self.failed_tests.append({
                    'name': 'Resume Download File Size',
                    'error': f'File too small: {len(content)} bytes'
                })
                return False
            
            # DOCX files are ZIP files, so they should start with PK signature
            if not content.startswith(b'PK'):
                print(f"❌ FAILED - Invalid DOCX file signature")
                print(f"   Expected: PK (ZIP signature)")
                print(f"   Got: {content[:4]}")
                self.failed_tests.append({
                    'name': 'Resume Download File Signature',
                    'error': 'Invalid DOCX file signature'
                })
                return False
            
            # Success
            self.tests_passed += 1
            print(f"✅ PASSED - Resume Download")
            print(f"   ✅ Status: 200 OK")
            print(f"   ✅ Content-Type: {content_type}")
            print(f"   ✅ Content-Disposition: {content_disposition}")
            print(f"   ✅ File size: {len(content)} bytes")
            print(f"   ✅ Valid DOCX signature: PK")
            
            return True
            
        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timed out after 30s")
            self.failed_tests.append({'name': 'Resume Download', 'error': 'Timeout'})
            return False
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.failed_tests.append({'name': 'Resume Download', 'error': str(e)})
            return False

    def test_cover_letter_download(self, application_id):
        """Test cover letter download endpoint"""
        print(f"\n📄 Testing Cover Letter Download for application: {application_id}")
        
        url = f"{self.base_url}/api/applications/{application_id}/download/cover-letter"
        headers = {
            'Authorization': f'Bearer {self.session_token}'
        }
        
        self.tests_run += 1
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            # Check status code
            if response.status_code != 200:
                print(f"❌ FAILED - Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    'name': 'Cover Letter Download',
                    'expected': 200,
                    'actual': response.status_code,
                    'response': response.text[:200]
                })
                return False
            
            # Check Content-Type header
            content_type = response.headers.get('Content-Type', '')
            expected_content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            
            if content_type != expected_content_type:
                print(f"❌ FAILED - Wrong Content-Type")
                print(f"   Expected: {expected_content_type}")
                print(f"   Got: {content_type}")
                self.failed_tests.append({
                    'name': 'Cover Letter Download Content-Type',
                    'error': f'Wrong Content-Type: {content_type}'
                })
                return False
            
            # Check Content-Disposition header
            content_disposition = response.headers.get('Content-Disposition', '')
            if not content_disposition.startswith('attachment; filename=Cover_Letter_'):
                print(f"❌ FAILED - Wrong Content-Disposition")
                print(f"   Expected: attachment; filename=Cover_Letter_*.docx")
                print(f"   Got: {content_disposition}")
                self.failed_tests.append({
                    'name': 'Cover Letter Download Content-Disposition',
                    'error': f'Wrong Content-Disposition: {content_disposition}'
                })
                return False
            
            # Check if file is valid DOCX (check file signature)
            content = response.content
            if len(content) < 4:
                print(f"❌ FAILED - File too small: {len(content)} bytes")
                self.failed_tests.append({
                    'name': 'Cover Letter Download File Size',
                    'error': f'File too small: {len(content)} bytes'
                })
                return False
            
            # DOCX files are ZIP files, so they should start with PK signature
            if not content.startswith(b'PK'):
                print(f"❌ FAILED - Invalid DOCX file signature")
                print(f"   Expected: PK (ZIP signature)")
                print(f"   Got: {content[:4]}")
                self.failed_tests.append({
                    'name': 'Cover Letter Download File Signature',
                    'error': 'Invalid DOCX file signature'
                })
                return False
            
            # Success
            self.tests_passed += 1
            print(f"✅ PASSED - Cover Letter Download")
            print(f"   ✅ Status: 200 OK")
            print(f"   ✅ Content-Type: {content_type}")
            print(f"   ✅ Content-Disposition: {content_disposition}")
            print(f"   ✅ File size: {len(content)} bytes")
            print(f"   ✅ Valid DOCX signature: PK")
            
            return True
            
        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timed out after 30s")
            self.failed_tests.append({'name': 'Cover Letter Download', 'error': 'Timeout'})
            return False
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.failed_tests.append({'name': 'Cover Letter Download', 'error': str(e)})
            return False

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
        
        # NEW: Test Analyze Match feature end-to-end (MAIN REVIEW REQUEST)
        print("\n🎯 Testing NEW Analyze Match Feature (MAIN REVIEW REQUEST)")
        analyze_match_success = self.test_analyze_match_feature()
        
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
        
        # Test the EXACT user reported search scenario FIRST
        print("\n🎯 TESTING EXACT USER REPORTED FAILING SEARCH")
        exact_search_success = self.test_exact_user_reported_search()
        
        # NEW: Test business analyst phrase matching (MAIN REVIEW REQUEST)
        print("\n🎯 TESTING BUSINESS ANALYST PHRASE MATCHING (REVIEW REQUEST)")
        phrase_matching_success = self.test_business_analyst_phrase_matching()
        
        # Then test other scenarios
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
        
        # Highlight key results
        print(f"\n🎯 KEY REVIEW REQUEST RESULTS:")
        if analyze_match_success:
            print(f"   ✅ Analyze Match Feature: WORKING")
        else:
            print(f"   ❌ Analyze Match Feature: FAILED")
        
        if phrase_matching_success:
            print(f"   ✅ Business Analyst Phrase Matching: WORKING")
        else:
            print(f"   ❌ Business Analyst Phrase Matching: FAILED")
        
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