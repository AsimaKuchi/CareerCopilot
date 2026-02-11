#!/usr/bin/env python3

import requests
import sys

def test_download_edge_cases():
    """Test download endpoints with edge cases and error conditions"""
    base_url = "https://job-autofill-pro.preview.emergentagent.com"
    session_token = "test_session_1768797070346"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session_token}'
    }
    
    print("🚀 Testing Download Endpoints - Edge Cases")
    print("="*50)
    
    # Test 1: Application without optimized_resume
    print("\n🔍 Test 1: Application without optimized_resume")
    app_data_no_resume = {
        "job_id": "test_no_resume",
        "job_title": "Test Job",
        "company": "Test Company",
        "location": "Remote",
        "job_description": "Test description",
        "cover_letter": "Test cover letter content"
        # No optimized_resume field
    }
    
    try:
        response = requests.post(f"{base_url}/api/applications", json=app_data_no_resume, headers=headers, timeout=30)
        if response.status_code == 200:
            app_id = response.json().get('application_id')
            print(f"   Created application: {app_id}")
            
            # Try to download resume (should fail)
            resume_response = requests.get(f"{base_url}/api/applications/{app_id}/download/resume", headers=headers, timeout=30)
            print(f"   Resume download status: {resume_response.status_code}")
            if resume_response.status_code == 400:
                print(f"   ✅ Correctly returns 400 for missing resume")
            else:
                print(f"   ❌ Expected 400, got {resume_response.status_code}")
        else:
            print(f"   ❌ Failed to create application: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 2: Application without cover_letter
    print("\n🔍 Test 2: Application without cover_letter")
    app_data_no_cover = {
        "job_id": "test_no_cover",
        "job_title": "Test Job",
        "company": "Test Company", 
        "location": "Remote",
        "job_description": "Test description",
        "optimized_resume": "Test resume content"
        # No cover_letter field
    }
    
    try:
        response = requests.post(f"{base_url}/api/applications", json=app_data_no_cover, headers=headers, timeout=30)
        if response.status_code == 200:
            app_id = response.json().get('application_id')
            print(f"   Created application: {app_id}")
            
            # Try to download cover letter (should fail)
            cover_response = requests.get(f"{base_url}/api/applications/{app_id}/download/cover-letter", headers=headers, timeout=30)
            print(f"   Cover letter download status: {cover_response.status_code}")
            if cover_response.status_code == 400:
                print(f"   ✅ Correctly returns 400 for missing cover letter")
            else:
                print(f"   ❌ Expected 400, got {cover_response.status_code}")
        else:
            print(f"   ❌ Failed to create application: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 3: Non-existent application
    print("\n🔍 Test 3: Non-existent application")
    fake_app_id = "app_nonexistent123"
    
    try:
        # Try to download from non-existent application
        resume_response = requests.get(f"{base_url}/api/applications/{fake_app_id}/download/resume", headers=headers, timeout=30)
        print(f"   Resume download status: {resume_response.status_code}")
        if resume_response.status_code == 404:
            print(f"   ✅ Correctly returns 404 for non-existent application")
        else:
            print(f"   ❌ Expected 404, got {resume_response.status_code}")
            
        cover_response = requests.get(f"{base_url}/api/applications/{fake_app_id}/download/cover-letter", headers=headers, timeout=30)
        print(f"   Cover letter download status: {cover_response.status_code}")
        if cover_response.status_code == 404:
            print(f"   ✅ Correctly returns 404 for non-existent application")
        else:
            print(f"   ❌ Expected 404, got {cover_response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 4: Authentication issues
    print("\n🔍 Test 4: Authentication issues")
    invalid_headers = {'Authorization': 'Bearer invalid_token'}
    
    try:
        # Try with invalid token
        response = requests.get(f"{base_url}/api/applications/any_id/download/resume", headers=invalid_headers, timeout=30)
        print(f"   Invalid auth status: {response.status_code}")
        if response.status_code == 401:
            print(f"   ✅ Correctly returns 401 for invalid authentication")
        else:
            print(f"   ❌ Expected 401, got {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "="*50)
    print("📊 EDGE CASE TESTING COMPLETE")
    print("="*50)

if __name__ == "__main__":
    test_download_edge_cases()