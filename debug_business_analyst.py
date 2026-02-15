#!/usr/bin/env python3

import requests
import json
import time

def test_business_analyst_search():
    """Debug the business analyst search specifically"""
    
    base_url = "https://auto-apply-hub-2.preview.emergentagent.com"
    session_token = "test_session_1768797070346"
    
    url = f"{base_url}/api/jobs/greenhouse/search"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session_token}',
        'Accept': 'text/event-stream'
    }
    
    # Test different variations
    test_cases = [
        {"query": "business analyst", "location": "greater toronto area, ontario"},
        {"query": "business analyst", "location": "toronto"},
        {"query": "business analyst", "location": ""},
        {"query": "analyst", "location": "toronto"},
        {"query": "business", "location": "toronto"},
    ]
    
    for i, search_data in enumerate(test_cases):
        print(f"\n{'='*60}")
        print(f"TEST CASE {i+1}: query='{search_data['query']}', location='{search_data['location']}'")
        print('='*60)
        
        jobs_found = []
        start_time = time.time()
        
        try:
            response = requests.post(url, json=search_data, headers=headers, stream=True, timeout=60)
            
            if response.status_code != 200:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                continue
            
            print(f"✅ HTTP 200 - Processing stream...")
            
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
                            print(f"✅ Completion: {total_jobs} jobs in {elapsed:.2f}s")
                            break
                        else:
                            jobs_found.append({
                                'title': data.get('title', 'N/A'),
                                'company': data.get('company', 'N/A'),
                                'location': data.get('location', 'N/A')
                            })
                    
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        continue
            
            # Show results
            print(f"\n📋 JOBS FOUND: {len(jobs_found)}")
            if jobs_found:
                for j, job in enumerate(jobs_found[:10]):
                    title_lower = job['title'].lower()
                    has_business = 'business' in title_lower
                    has_analyst = 'analyst' in title_lower
                    match_indicator = ""
                    if has_business and has_analyst:
                        match_indicator = " ✅ BOTH"
                    elif has_business:
                        match_indicator = " 🔵 BUSINESS"
                    elif has_analyst:
                        match_indicator = " 🟡 ANALYST"
                    
                    print(f"   {j+1}. {job['title']} at {job['company']}{match_indicator}")
                    print(f"      Location: {job['location']}")
                
                if len(jobs_found) > 10:
                    print(f"   ... and {len(jobs_found) - 10} more jobs")
            else:
                print("   No jobs found")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_business_analyst_search()