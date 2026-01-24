#!/usr/bin/env python3

import requests
import json
import time

def test_and_check_logs():
    base_url = "https://jobsmart-8.preview.emergentagent.com"
    session_token = "test_session_1768797070346"
    
    print("🔍 Testing Greenhouse endpoint and checking logs...")
    
    url = f"{base_url}/api/jobs/greenhouse/search"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session_token}',
        'Accept': 'text/event-stream'
    }
    
    search_data = {
        "query": "test",
        "location": "test"
    }
    
    # Make a quick request to trigger logging
    try:
        response = requests.post(url, json=search_data, headers=headers, stream=True, timeout=10)
        
        # Read just a few lines to trigger the log message
        count = 0
        for line in response.iter_lines(decode_unicode=True):
            count += 1
            if count > 5:  # Just read a few lines
                break
        
        print("✅ Request completed")
        
    except Exception as e:
        print(f"Request error: {e}")
    
    # Now check logs
    print("\n🔍 Checking backend logs...")
    
    import subprocess
    result = subprocess.run(
        ['tail', '-n', '50', '/var/log/supervisor/backend.err.log'],
        capture_output=True, text=True, timeout=10
    )
    
    if result.returncode == 0:
        log_content = result.stdout
        if "Show ALL jobs matching query/location" in log_content:
            print("✅ Found expected log message: 'Show ALL jobs matching query/location'")
            # Show the specific line
            lines = log_content.split('\n')
            for line in lines:
                if "Show ALL jobs matching query/location" in line:
                    print(f"   Log line: {line}")
            return True
        else:
            print("❌ Log message not found")
            return False
    else:
        print("❌ Could not read logs")
        return False

if __name__ == "__main__":
    test_and_check_logs()