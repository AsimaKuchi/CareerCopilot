#!/usr/bin/env python3

import requests
import json

def test_backend_job_search_debug():
    """Debug the backend job search endpoint"""
    
    base_url = "https://jobsmart-8.preview.emergentagent.com"
    session_token = "test_session_1768797070346"
    
    url = f"{base_url}/api/jobs/search"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session_token}'
    }
    
    search_data = {
        "query": "engineer",
        "location": ""
    }
    
    try:
        print("🔍 Testing backend job search with debug info...")
        print(f"URL: {url}")
        print(f"Headers: {headers}")
        print(f"Data: {json.dumps(search_data, indent=2)}")
        
        response = requests.post(url, json=search_data, headers=headers, timeout=60)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Data: {json.dumps(data, indent=2)}")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_backend_job_search_debug()