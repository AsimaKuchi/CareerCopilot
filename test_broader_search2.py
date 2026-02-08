#!/usr/bin/env python3

import requests
import json
import time

def test_broader_analyst_search():
    """Test broader analyst searches to understand job availability"""
    
    base_url = "https://resume-first-jobs-1.preview.emergentagent.com"
    session_token = "test_session_1768797070346"
    
    url = f"{base_url}/api/jobs/greenhouse/search"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session_token}',
        'Accept': 'text/event-stream'
    }
    
    # Test different search variations
    test_scenarios = [
        {
            "name": "Just 'analyst' in Toronto",
            "query": "analyst",
            "location": "toronto"
        },
        {
            "name": "Just 'analyst' (no location)",
            "query": "analyst", 
            "location": ""
        },
        {
            "name": "All jobs in Toronto",
            "query": "",
            "location": "toronto"
        },
        {
            "name": "Business analyst (no location)",
            "query": "business analyst",
            "location": ""
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n🔍 TESTING: {scenario['name']}")
        print("="*50)
        print(f"Query: '{scenario['query']}'")
        print(f"Location: '{scenario['location']}'")
        
        search_data = {
            "query": scenario['query'],
            "location": scenario['location']
        }
        
        jobs_count = 0
        analyst_jobs = []
        toronto_jobs = []
        
        try:
            response = requests.post(url, json=search_data, headers=headers, stream=True, timeout=70)
            
            if response.status_code != 200:
                print(f"❌ Request failed with status {response.status_code}")
                continue
            
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    data_str = line[6:]
                    try:
                        data = json.loads(data_str)
                        
                        if data.get('heartbeat') or data.get('progress'):
                            continue
                        
                        if data.get('done'):
                            total_jobs = data.get('total', 0)
                            print(f"✅ Total jobs: {total_jobs}")
                            break
                        else:
                            jobs_count += 1
                            title = data.get('title', '').lower()
                            location = data.get('location', '').lower()
                            company = data.get('company', '')
                            
                            # Track analyst jobs
                            if 'analyst' in title:
                                analyst_jobs.append({
                                    'title': data.get('title'),
                                    'company': company,
                                    'location': data.get('location')
                                })
                            
                            # Track Toronto jobs
                            if 'toronto' in location:
                                toronto_jobs.append({
                                    'title': data.get('title'),
                                    'company': company,
                                    'location': data.get('location')
                                })
                    
                    except json.JSONDecodeError:
                        continue
            
            print(f"Analyst jobs found: {len(analyst_jobs)}")
            print(f"Toronto jobs found: {len(toronto_jobs)}")
            
            # Show sample analyst jobs
            if analyst_jobs:
                print("Sample analyst jobs:")
                for i, job in enumerate(analyst_jobs[:5]):
                    print(f"  {i+1}. {job['title']} at {job['company']} ({job['location']})")
            
            # Show sample Toronto jobs
            if toronto_jobs and scenario['location'] != 'toronto':
                print("Sample Toronto jobs:")
                for i, job in enumerate(toronto_jobs[:3]):
                    print(f"  {i+1}. {job['title']} at {job['company']} ({job['location']})")
        
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_broader_analyst_search()