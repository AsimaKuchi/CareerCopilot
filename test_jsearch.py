#!/usr/bin/env python3

import requests
import json

def test_jsearch_api():
    """Test JSearch API endpoint specifically"""
    base_url = "https://resume-first-jobs-1.preview.emergentagent.com"
    session_token = "test_session_1768797070346"
    
    print("🔍 TESTING JSEARCH API ENDPOINT")
    print("="*50)
    
    url = f"{base_url}/api/jobs/search"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session_token}'
    }
    
    search_data = {
        "query": "engineer",
        "location": ""
    }
    
    print(f"🔍 Making request to: {url}")
    print(f"📋 Request data: {search_data}")
    print()
    
    try:
        response = requests.post(url, json=search_data, headers=headers, timeout=60)
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        data = response.json()
        jobs = data.get('jobs', [])
        total = data.get('total', 0)
        
        print(f"✅ Response received")
        print(f"📊 Jobs found: {len(jobs)}")
        print(f"📊 Total reported: {total}")
        print()
        
        if len(jobs) == 0:
            print("❌ NO JOBS FOUND - This indicates an issue with JSearch API")
            print("Possible causes:")
            print("  - JSearch API key issues")
            print("  - API rate limiting")
            print("  - Network connectivity issues")
            print("  - API endpoint changes")
            return
        
        # Show sample jobs
        print("📋 SAMPLE JOBS:")
        for i, job in enumerate(jobs[:5], 1):
            title = job.get('title', 'N/A')
            company = job.get('company', 'N/A')
            location = job.get('location', 'N/A')
            source = job.get('source', 'N/A')
            match_score = job.get('match_score', 'N/A')
            
            print(f"  {i}. {title}")
            print(f"     Company: {company}")
            print(f"     Location: {location}")
            print(f"     Source: {source}")
            print(f"     Match Score: {match_score}")
            print()
        
        # Check job structure
        print("🔍 CHECKING JOB STRUCTURE:")
        required_fields = ['job_id', 'title', 'company', 'match_score', 'match_strengths', 'match_gaps']
        
        if jobs:
            sample_job = jobs[0]
            for field in required_fields:
                has_field = field in sample_job
                status = "✅" if has_field else "❌"
                print(f"{status} {field}: {'Present' if has_field else 'Missing'}")
        
        print()
        
        # Final assessment
        has_jobs = len(jobs) > 0
        proper_structure = all(field in jobs[0] for field in required_fields) if jobs else False
        
        print("🏁 FINAL ASSESSMENT:")
        print(f"✅ Jobs returned: {'YES' if has_jobs else 'NO'}")
        print(f"✅ Proper structure: {'YES' if proper_structure else 'NO'}")
        
        if has_jobs and proper_structure:
            print("🎉 SUCCESS: JSearch API working correctly!")
        else:
            print("❌ ISSUES FOUND: JSearch API has problems")
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")

if __name__ == "__main__":
    test_jsearch_api()