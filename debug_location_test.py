#!/usr/bin/env python3

import requests
import json
import time

def test_location_matching_debug():
    """Debug the location matching for the specific user reported search"""
    
    base_url = "https://job-autofill-pro.preview.emergentagent.com"
    session_token = "test_session_1768797070346"
    
    url = f"{base_url}/api/jobs/greenhouse/search"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session_token}',
        'Accept': 'text/event-stream'
    }
    
    # Test the exact search that was reported as failing
    search_data = {
        "query": "business analyst",
        "location": "greater toronto area, ontario"
    }
    
    print("🔍 DEBUGGING LOCATION MATCHING")
    print("="*50)
    print(f"Query: '{search_data['query']}'")
    print(f"Location: '{search_data['location']}'")
    print(f"Expected: Location keywords should be ['toronto', 'ontario']")
    print()
    
    jobs_found = []
    locations_seen = set()
    companies_with_jobs = set()
    
    try:
        response = requests.post(url, json=search_data, headers=headers, stream=True, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ Request failed: {response.status_code}")
            return
        
        print("✅ Streaming response received")
        print()
        
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                data_str = line[6:]
                try:
                    data = json.loads(data_str)
                    
                    if data.get('heartbeat') or data.get('progress'):
                        continue
                    
                    if data.get('done'):
                        total = data.get('total', 0)
                        print(f"✅ Search completed: {total} jobs found")
                        break
                    else:
                        jobs_found.append(data)
                        job_location = data.get('location', 'No location')
                        locations_seen.add(job_location)
                        companies_with_jobs.add(data.get('company', 'Unknown'))
                        
                        print(f"Job {len(jobs_found)}: {data.get('title', 'No title')}")
                        print(f"  Company: {data.get('company', 'Unknown')}")
                        print(f"  Location: {job_location}")
                        print(f"  Match Score: {data.get('match_score', 'N/A')}")
                        print()
                        
                except json.JSONDecodeError:
                    continue
        
        print("="*50)
        print("ANALYSIS RESULTS")
        print("="*50)
        print(f"Total jobs found: {len(jobs_found)}")
        print(f"Companies with matching jobs: {len(companies_with_jobs)}")
        print(f"Unique locations seen: {len(locations_seen)}")
        print()
        
        print("Companies with jobs:")
        for company in sorted(companies_with_jobs):
            print(f"  - {company}")
        print()
        
        print("All locations seen:")
        for location in sorted(locations_seen):
            print(f"  - {location}")
        print()
        
        # Check if any locations contain toronto/ontario keywords
        toronto_locations = [loc for loc in locations_seen if 'toronto' in loc.lower()]
        ontario_locations = [loc for loc in locations_seen if 'ontario' in loc.lower()]
        canada_locations = [loc for loc in locations_seen if 'canada' in loc.lower()]
        
        print("Location keyword analysis:")
        print(f"  Locations with 'toronto': {len(toronto_locations)}")
        for loc in toronto_locations:
            print(f"    - {loc}")
        print(f"  Locations with 'ontario': {len(ontario_locations)}")  
        for loc in ontario_locations:
            print(f"    - {loc}")
        print(f"  Locations with 'canada': {len(canada_locations)}")
        for loc in canada_locations:
            print(f"    - {loc}")
        
        # Now test with just "business analyst" and no location to see total available
        print("\n" + "="*50)
        print("TESTING WITHOUT LOCATION FILTER")
        print("="*50)
        
        search_data_no_location = {
            "query": "business analyst", 
            "location": ""
        }
        
        print("Testing same query without location filter...")
        
        response2 = requests.post(url, json=search_data_no_location, headers=headers, stream=True, timeout=60)
        
        if response2.status_code == 200:
            jobs_no_location = 0
            for line in response2.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    data_str = line[6:]
                    try:
                        data = json.loads(data_str)
                        if data.get('done'):
                            print(f"✅ Without location filter: {data.get('total', 0)} jobs found")
                            break
                        elif not data.get('heartbeat') and not data.get('progress'):
                            jobs_no_location += 1
                    except json.JSONDecodeError:
                        continue
        
        print("\n" + "="*50)
        print("CONCLUSION")
        print("="*50)
        
        if len(jobs_found) < 40:
            print("❌ ISSUE CONFIRMED: Not enough jobs found with location filter")
            print(f"   Expected: 40+ jobs")
            print(f"   Actual: {len(jobs_found)} jobs")
            print()
            print("Possible causes:")
            print("1. Location matching is too strict")
            print("2. Not enough business analyst jobs in Toronto/Ontario area")
            print("3. Jobs don't have proper location data")
            print("4. Location keywords extraction not working correctly")
        else:
            print("✅ Expected number of jobs found")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_location_matching_debug()