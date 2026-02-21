#!/usr/bin/env python3

import requests
import json
import time

def test_global_business_analyst_search():
    """Search for business analyst jobs globally to see if any exist"""
    
    base_url = "https://copilot-ai-7.preview.emergentagent.com"
    session_token = "test_session_1768797070346"
    
    url = f"{base_url}/api/jobs/greenhouse/search"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session_token}',
        'Accept': 'text/event-stream'
    }
    
    # Search globally for business analyst
    search_data = {"query": "business analyst", "location": ""}
    
    print("🔍 Searching GLOBALLY for 'business analyst' jobs...")
    print("This will help us understand if the issue is location-specific or if no business analyst jobs exist")
    
    jobs_found = []
    business_analyst_jobs = []
    start_time = time.time()
    
    try:
        response = requests.post(url, json=search_data, headers=headers, stream=True, timeout=90)
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            return
        
        print(f"✅ HTTP 200 - Processing stream...")
        
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
                        print(f"✅ Completion: {total_jobs} jobs in {elapsed:.2f}s")
                        break
                    else:
                        jobs_found.append({
                            'title': data.get('title', 'N/A'),
                            'company': data.get('company', 'N/A'),
                            'location': data.get('location', 'N/A')
                        })
                        
                        # Check if this is a true business analyst job
                        title_lower = data.get('title', '').lower()
                        if 'business' in title_lower and 'analyst' in title_lower:
                            business_analyst_jobs.append({
                                'title': data.get('title', 'N/A'),
                                'company': data.get('company', 'N/A'),
                                'location': data.get('location', 'N/A')
                            })
                
                except json.JSONDecodeError:
                    continue
        
        # Show results
        print(f"\n📊 RESULTS SUMMARY:")
        print(f"   Total jobs found: {len(jobs_found)}")
        print(f"   True 'Business Analyst' jobs: {len(business_analyst_jobs)}")
        
        if business_analyst_jobs:
            print(f"\n✅ BUSINESS ANALYST JOBS FOUND ({len(business_analyst_jobs)}):")
            for i, job in enumerate(business_analyst_jobs):
                print(f"   {i+1}. {job['title']} at {job['company']}")
                print(f"      Location: {job['location']}")
        else:
            print(f"\n❌ NO TRUE BUSINESS ANALYST JOBS FOUND")
            print(f"   This explains why the Toronto search returned 0 results")
            print(f"   The phrase matching is working correctly, but no jobs match the criteria")
        
        # Show what jobs were found instead
        if jobs_found and not business_analyst_jobs:
            print(f"\n📋 OTHER JOBS FOUND (first 10):")
            for i, job in enumerate(jobs_found[:10]):
                title_lower = job['title'].lower()
                has_business = 'business' in title_lower
                has_analyst = 'analyst' in title_lower
                match_indicator = ""
                if has_business and has_analyst:
                    match_indicator = " ✅ BOTH"
                elif has_business:
                    match_indicator = " 🔵 BUSINESS ONLY"
                elif has_analyst:
                    match_indicator = " 🟡 ANALYST ONLY"
                else:
                    match_indicator = " ❓ NEITHER"
                
                print(f"   {i+1}. {job['title']}{match_indicator}")
                print(f"      Company: {job['company']}, Location: {job['location']}")
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_global_business_analyst_search()