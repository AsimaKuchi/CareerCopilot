#!/usr/bin/env python3

import requests
import sys

def test_specific_application():
    """Test download endpoints with a specific application ID from logs"""
    base_url = "https://job-autofill-2.preview.emergentagent.com"
    session_token = "test_session_1768797070346"
    
    # Application ID from the logs that had successful downloads
    app_id = "app_89854a2050df"
    
    headers = {
        'Authorization': f'Bearer {session_token}'
    }
    
    print(f"🔍 Testing downloads for application: {app_id}")
    
    # Test resume download
    print(f"\n📄 Testing Resume Download...")
    resume_url = f"{base_url}/api/applications/{app_id}/download/resume"
    print(f"   URL: {resume_url}")
    
    try:
        response = requests.get(resume_url, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"   Content-Disposition: {response.headers.get('Content-Disposition', 'N/A')}")
        
        if response.status_code == 200:
            content = response.content
            print(f"   File size: {len(content)} bytes")
            print(f"   File signature: {content[:4] if len(content) >= 4 else 'N/A'}")
            
            # Check DOCX signature
            if content.startswith(b'PK'):
                print(f"   ✅ Valid DOCX file signature")
            else:
                print(f"   ❌ Invalid DOCX file signature")
        else:
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test cover letter download
    print(f"\n📄 Testing Cover Letter Download...")
    cover_url = f"{base_url}/api/applications/{app_id}/download/cover-letter"
    print(f"   URL: {cover_url}")
    
    try:
        response = requests.get(cover_url, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"   Content-Disposition: {response.headers.get('Content-Disposition', 'N/A')}")
        
        if response.status_code == 200:
            content = response.content
            print(f"   File size: {len(content)} bytes")
            print(f"   File signature: {content[:4] if len(content) >= 4 else 'N/A'}")
            
            # Check DOCX signature
            if content.startswith(b'PK'):
                print(f"   ✅ Valid DOCX file signature")
            else:
                print(f"   ❌ Invalid DOCX file signature")
        else:
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

if __name__ == "__main__":
    test_specific_application()