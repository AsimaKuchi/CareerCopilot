#!/usr/bin/env python3

import requests
import json
import time

def test_exact_user_search():
    """Test the EXACT search scenario from review request"""
    base_url = "https://careerwise-7.preview.emergentagent.com"
    session_token = "test_session_1768797070346"
    
    print("🎯 TESTING EXACT USER SEARCH SCENARIO")
    print("="*60)
    print("Query: 'business analyst'")
    print("Location: 'greater toronto area, ontario'")
    print("Expected: 12+ jobs from Stripe alone, 10-20+ total")
    print("Expected location matching: ['toronto', 'ontario', 'canada']")
    print()
    
    url = f"{base_url}/api/jobs/greenhouse/search"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session_token}',
        'Accept': 'text/event-stream'
    }
    
    search_data = {
        "query": "business analyst",
        "location": "greater toronto area, ontario"
    }
    
    print(f"🔍 Making request to: {url}")
    print(f"📋 Search data: {search_data}")
    print()
    
    start_time = time.time()
    jobs_received = 0
    stripe_jobs = []
    canada_jobs = []
    remote_jobs = []
    all_jobs = []
    
    try:
        response = requests.post(url, json=search_data, headers=headers, stream=True, timeout=70)
        
        print(f"📡 Response status: {response.status_code}")
        print(f"📡 Content-Type: {response.headers.get('content-type', 'N/A')}")
        print()
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return
        
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
                        print(f"✅ Streaming completed: {total_jobs} jobs in {elapsed:.2f}s")
                        break
                    else:
                        jobs_received += 1
                        all_jobs.append(data)
                        
                        # Analyze job details
                        title = data.get('title', '')
                        company = data.get('company', '')
                        location = data.get('location', '')
                        source = data.get('source', '')
                        
                        # Track Stripe jobs specifically
                        if 'stripe' in company.lower():
                            stripe_jobs.append(data)
                        
                        # Track Canada/Toronto jobs
                        location_lower = location.lower()
                        if any(keyword in location_lower for keyword in ['toronto', 'ontario', 'canada']):
                            canada_jobs.append(data)
                        
                        # Track remote jobs
                        if 'remote' in location_lower:
                            remote_jobs.append(data)
                        
                        # Show first 10 jobs for analysis
                        if jobs_received <= 10:
                            print(f"Job {jobs_received:2d}: {title}")
                            print(f"         Company: {company}")
                            print(f"         Location: {location}")
                            print(f"         Source: {source}")
                            print(f"         Match Score: {data.get('match_score', 'N/A')}")
                            print()
                
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON: {data_str[:100]}")
                    continue
        
        elapsed_total = time.time() - start_time
        
        # Analysis and Results
        print("="*60)
        print("📊 SEARCH RESULTS ANALYSIS")
        print("="*60)
        print(f"Total jobs found: {jobs_received}")
        print(f"Stripe jobs: {len(stripe_jobs)}")
        print(f"Canada/Toronto jobs: {len(canada_jobs)}")
        print(f"Remote jobs: {len(remote_jobs)}")
        print(f"Response time: {elapsed_total:.2f}s")
        print()
        
        # Expected vs Actual
        print("🎯 EXPECTATIONS vs REALITY:")
        print(f"Expected total jobs: 10-20+")
        print(f"Actual total jobs: {jobs_received}")
        print(f"✅ Met expectation: {'YES' if jobs_received >= 10 else 'NO'}")
        print()
        
        print(f"Expected Stripe jobs: 12+")
        print(f"Actual Stripe jobs: {len(stripe_jobs)}")
        print(f"✅ Met expectation: {'YES' if len(stripe_jobs) >= 12 else 'NO'}")
        print()
        
        # Show Stripe jobs specifically
        if stripe_jobs:
            print("🏢 STRIPE JOBS FOUND:")
            for i, job in enumerate(stripe_jobs, 1):
                title = job.get('title', 'N/A')
                location = job.get('location', 'N/A')
                print(f"  {i}. {title} - {location}")
        else:
            print("❌ NO STRIPE JOBS FOUND")
        print()
        
        # Show Canada/Toronto jobs
        if canada_jobs:
            print("🇨🇦 CANADA/TORONTO JOBS FOUND:")
            for i, job in enumerate(canada_jobs[:5], 1):  # Show first 5
                title = job.get('title', 'N/A')
                company = job.get('company', 'N/A')
                location = job.get('location', 'N/A')
                print(f"  {i}. {title} at {company} - {location}")
            if len(canada_jobs) > 5:
                print(f"  ... and {len(canada_jobs) - 5} more")
        else:
            print("❌ NO CANADA/TORONTO JOBS FOUND")
        print()
        
        # Location matching analysis
        print("🗺️  LOCATION MATCHING ANALYSIS:")
        location_keywords = set()
        for job in all_jobs:
            location = job.get('location', '').lower()
            if location:
                # Extract keywords from job locations
                words = location.replace(',', ' ').split()
                location_keywords.update(words)
        
        expected_keywords = ['toronto', 'ontario', 'canada']
        found_keywords = [kw for kw in expected_keywords if kw in location_keywords]
        
        print(f"Expected location keywords: {expected_keywords}")
        print(f"Found location keywords: {found_keywords}")
        print(f"Location matching working: {'YES' if found_keywords else 'NO'}")
        print()
        
        # Final verdict
        print("="*60)
        print("🏁 FINAL VERDICT")
        print("="*60)
        
        success_criteria = [
            (jobs_received >= 10, f"Total jobs ≥ 10: {jobs_received}"),
            (len(stripe_jobs) >= 1, f"Stripe jobs found: {len(stripe_jobs)}"),
            (len(canada_jobs) >= 1, f"Canada/Toronto jobs: {len(canada_jobs)}"),
            (elapsed_total < 60, f"Response time < 60s: {elapsed_total:.2f}s")
        ]
        
        passed = sum(1 for criteria, _ in success_criteria if criteria)
        total = len(success_criteria)
        
        for criteria, description in success_criteria:
            status = "✅" if criteria else "❌"
            print(f"{status} {description}")
        
        print()
        print(f"Overall: {passed}/{total} criteria met")
        
        if passed == total:
            print("🎉 SUCCESS: All criteria met!")
        elif passed >= 3:
            print("⚠️  PARTIAL SUCCESS: Most criteria met")
        else:
            print("❌ FAILURE: Major issues found")
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")

if __name__ == "__main__":
    test_exact_user_search()