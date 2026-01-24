#!/usr/bin/env python3

import requests
import json
import time
from datetime import datetime

class GreenhouseStreamingTester:
    def __init__(self, base_url="https://jobsmart-8.preview.emergentagent.com"):
        self.base_url = base_url
        self.session_token = "test_session_1768797070346"  # From auth setup

    def test_greenhouse_streaming_scenarios(self):
        """Test Greenhouse SSE streaming with specific scenarios from review request"""
        print("="*60)
        print("🌿 TESTING GREENHOUSE STREAMING - SIMPLIFIED FILTERING")
        print("="*60)
        
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
        
        print(f"   Query: '{search_data['query']}', Location: '{search_data['location']}'")
        
        start_time = time.time()
        jobs_received = 0
        completion_received = False
        first_job_time = None
        greenhouse_sources = set()
        jobs_with_match_data = 0
        
        try:
            response = requests.post(url, json=search_data, headers=headers, stream=True, timeout=70)
            
            # Check response headers
            content_type = response.headers.get('content-type', '')
            if 'text/event-stream' not in content_type:
                print(f"❌ FAILED - Expected text/event-stream, got {content_type}")
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
                            if data.get('progress'):
                                checked = data.get('checked', 0)
                                found = data.get('found', 0)
                                print(f"   Progress: {checked} companies checked, {found} jobs found so far")
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
                return False
            
            # Success
            print(f"✅ PASSED - {scenario['name']}")
            print(f"   ✅ Jobs returned: {jobs_received} (≥ {scenario['expected_min_jobs']} expected)")
            print(f"   ✅ Quality sources: {', '.join(greenhouse_sources)}")
            print(f"   ✅ Jobs with match data: {jobs_with_match_data}/{jobs_received}")
            print(f"   ✅ Response time: {elapsed_total:.2f}s")
            print(f"   ✅ First job time: {first_job_time:.2f}s")
            
            return True
            
        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timed out after 70s")
            return False
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            return False

    def check_backend_logs(self):
        """Check backend logs for the expected message about simplified filtering"""
        print("\n🔍 Checking backend logs for simplified filtering message...")
        
        try:
            # Check supervisor backend error logs (where application logs go)
            import subprocess
            result = subprocess.run(
                ['tail', '-n', '100', '/var/log/supervisor/backend.err.log'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                log_content = result.stdout
                if "Show ALL jobs matching query/location" in log_content:
                    print("✅ Found expected log message: 'Show ALL jobs matching query/location'")
                    # Count occurrences to show activity
                    count = log_content.count("Show ALL jobs matching query/location")
                    print(f"   Message appears {count} times in recent logs (indicating active searches)")
                    return True
                else:
                    print("⚠️  Expected log message not found in recent logs")
                    print("   Looking for: 'Show ALL jobs matching query/location'")
                    # Show recent log lines for debugging
                    lines = log_content.split('\n')[-10:]
                    print("   Recent log lines:")
                    for line in lines:
                        if line.strip():
                            print(f"     {line}")
                    return False
            else:
                print("⚠️  Could not read backend logs")
                return False
                
        except Exception as e:
            print(f"⚠️  Error checking logs: {str(e)}")
            return False

def main():
    tester = GreenhouseStreamingTester()
    
    print("🚀 Starting Greenhouse Streaming Tests")
    print(f"📍 Base URL: {tester.base_url}")
    print(f"🔑 Session Token: {tester.session_token[:20]}...")
    
    start_time = datetime.now()
    
    # Run the specific tests requested in review
    success = tester.test_greenhouse_streaming_scenarios()
    
    # Check backend logs
    tester.check_backend_logs()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"⏱️  Duration: {duration:.2f} seconds")
    
    if success:
        print("✅ All Greenhouse streaming scenarios PASSED")
        print("🎯 Simplified filtering is working correctly")
        print("🌿 Jobs are streaming from quality sources (Greenhouse primarily)")
        print("📊 Match scores are being calculated for ranking")
        print("💪 Jobs have strengths/gaps for display")
    else:
        print("❌ Some Greenhouse streaming scenarios FAILED")
        print("🔧 Check the detailed output above for specific issues")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())