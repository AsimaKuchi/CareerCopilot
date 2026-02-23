#!/usr/bin/env python3

import requests
import json
import time
import sys

class GreenhouseStreamingTester:
    def __init__(self, base_url="https://job-autofill-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.session_token = "test_session_1768797070346"
        
    def test_streaming_with_query(self, query, location="", expected_min_jobs=5):
        """Test streaming with specific query parameters"""
        url = f"{self.base_url}/api/jobs/greenhouse/search"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.session_token}',
            'Accept': 'text/event-stream'
        }
        
        search_data = {
            "query": query,
            "location": location
        }
        
        print(f"\n🔍 Testing Greenhouse Streaming: '{query}' in '{location or 'Any location'}'")
        
        start_time = time.time()
        jobs_received = 0
        completion_received = False
        first_job_time = None
        job_details = []
        
        try:
            response = requests.post(url, json=search_data, headers=headers, stream=True, timeout=70)
            
            if response.status_code != 200:
                print(f"❌ FAILED - Status: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
            
            # Verify content type
            content_type = response.headers.get('content-type', '')
            if 'text/event-stream' not in content_type:
                print(f"❌ FAILED - Wrong content type: {content_type}")
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
                            print(f"✅ Completion: {total_jobs} jobs in {elapsed:.2f}s")
                            break
                        else:
                            jobs_received += 1
                            if first_job_time is None:
                                first_job_time = time.time() - start_time
                                print(f"✅ First job after {first_job_time:.2f}s")
                            
                            # Store job details for analysis
                            job_details.append({
                                'title': data.get('title', ''),
                                'company': data.get('company', ''),
                                'location': data.get('location', ''),
                                'match_score': data.get('match_score', 0),
                                'match_recommendation': data.get('match_recommendation', ''),
                                'match_strengths': data.get('match_strengths', []),
                                'match_gaps': data.get('match_gaps', [])
                            })
                            
                            # Show first few jobs
                            if jobs_received <= 5:
                                print(f"   Job {jobs_received}: {data.get('title', 'N/A')} at {data.get('company', 'N/A')}")
                                print(f"      Score: {data.get('match_score', 'N/A')}, Rec: {data.get('match_recommendation', 'N/A')}")
                                if data.get('match_strengths'):
                                    print(f"      Strengths: {data.get('match_strengths', [])[:2]}")
                    
                    except json.JSONDecodeError as e:
                        print(f"❌ Invalid JSON: {data_str[:100]}")
                        continue
            
            elapsed_total = time.time() - start_time
            
            # Analyze results
            success = True
            
            if not completion_received:
                print(f"❌ No completion message received")
                success = False
            
            if elapsed_total > 60:
                print(f"❌ Too slow: {elapsed_total:.2f}s")
                success = False
            
            if jobs_received < expected_min_jobs:
                print(f"⚠️  Only {jobs_received} jobs (expected {expected_min_jobs}+)")
            
            # Analyze job quality
            if job_details:
                avg_score = sum(job['match_score'] for job in job_details) / len(job_details)
                high_score_jobs = [job for job in job_details if job['match_score'] >= 70]
                companies = set(job['company'] for job in job_details)
                
                print(f"📊 Analysis:")
                print(f"   Average match score: {avg_score:.1f}")
                print(f"   High-score jobs (70+): {len(high_score_jobs)}")
                print(f"   Unique companies: {len(companies)}")
                print(f"   Sample companies: {list(companies)[:5]}")
                
                # Check for match scoring functionality
                jobs_with_strengths = [job for job in job_details if job['match_strengths']]
                jobs_with_gaps = [job for job in job_details if job['match_gaps']]
                
                print(f"   Jobs with strengths: {len(jobs_with_strengths)}")
                print(f"   Jobs with gaps: {len(jobs_with_gaps)}")
                
                if jobs_with_strengths:
                    print(f"   Sample strength: {jobs_with_strengths[0]['match_strengths'][0][:80]}...")
            
            if success:
                print(f"✅ PASSED - Streaming test successful")
            
            return success
            
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            return False

def main():
    tester = GreenhouseStreamingTester()
    
    print("🚀 Greenhouse Streaming Comprehensive Tests")
    print("=" * 60)
    
    test_cases = [
        ("engineer", "", 10),
        ("software engineer", "", 8),
        ("data scientist", "", 5),
        ("product manager", "", 5),
        ("designer", "", 3),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for query, location, min_jobs in test_cases:
        success = tester.test_streaming_with_query(query, location, min_jobs)
        if success:
            passed += 1
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "=" * 60)
    print(f"📊 FINAL RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Greenhouse streaming tests PASSED!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())