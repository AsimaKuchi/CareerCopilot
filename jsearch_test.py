#!/usr/bin/env python3

import requests
import json

def test_jsearch_direct():
    """Test JSearch API directly to see what's being returned"""
    
    headers = {
        "X-RapidAPI-Key": "fe79cf1565msh09f657b8930f39bp1930cbjsnaa07ed2d0cd8",
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    
    params = {
        "query": "engineer",
        "num_pages": "1",
        "page": "1"
    }
    
    try:
        print("🔍 Testing JSearch API directly...")
        response = requests.get(
            "https://jsearch.p.rapidapi.com/search",
            params=params,
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            jobs = data.get("data", [])
            
            print(f"Total jobs returned: {len(jobs)}")
            
            # Check for Bebee jobs
            bebee_jobs = [job for job in jobs if "bebee.com" in job.get("job_apply_link", "").lower()]
            non_bebee_jobs = [job for job in jobs if "bebee.com" not in job.get("job_apply_link", "").lower()]
            
            print(f"Bebee jobs: {len(bebee_jobs)}")
            print(f"Non-Bebee jobs: {len(non_bebee_jobs)}")
            
            if non_bebee_jobs:
                print(f"\nSample non-Bebee jobs:")
                for i, job in enumerate(non_bebee_jobs[:3]):
                    print(f"  {i+1}. {job.get('job_title')} at {job.get('employer_name')}")
                    print(f"     Apply: {job.get('job_apply_link')}")
            
            if bebee_jobs:
                print(f"\nSample Bebee jobs (filtered out):")
                for i, job in enumerate(bebee_jobs[:3]):
                    print(f"  {i+1}. {job.get('job_title')} at {job.get('employer_name')}")
                    print(f"     Apply: {job.get('job_apply_link')}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_jsearch_direct()