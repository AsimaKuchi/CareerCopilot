#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import time

class DownloadTester:
    def __init__(self, base_url="https://careerfit-30.preview.emergentagent.com"):
        self.base_url = base_url
        self.session_token = "test_session_1768797070346"  # From auth setup
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.session_token}'
        }

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Non-dict response'}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    'name': name,
                    'expected': expected_status,
                    'actual': response.status_code,
                    'response': response.text[:200]
                })

            return success, response.json() if success and response.text else {}

        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timed out after {timeout}s")
            self.failed_tests.append({'name': name, 'error': 'Timeout'})
            return False, {}
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.failed_tests.append({'name': name, 'error': str(e)})
            return False, {}

    def test_download_endpoints(self):
        """Test resume and cover letter download endpoints as requested in review"""
        print("\n" + "="*60)
        print("🎯 TESTING DOWNLOAD ENDPOINTS (REVIEW REQUEST)")
        print("="*60)
        print("Testing resume and cover letter download functionality")
        
        # Step 1: Get list of applications
        print("\n🔍 Step 1: Getting list of applications...")
        success, apps_response = self.run_test("Get Applications List", "GET", "applications", 200)
        
        if not success or not apps_response:
            print("❌ Cannot test downloads - no applications endpoint available")
            return False
        
        applications = apps_response.get('applications', [])
        if not applications:
            print("❌ No applications found - creating test application with resume and cover letter...")
            # Create a test application with optimized resume and cover letter
            return self.create_test_application_and_test_downloads()
        
        print(f"✅ Found {len(applications)} applications")
        
        # Step 2: Find applications with optimized_resume and cover_letter
        resume_app = None
        cover_letter_app = None
        
        for app in applications:
            print(f"   Application {app.get('application_id')}: has_resume={bool(app.get('optimized_resume'))}, has_cover_letter={bool(app.get('cover_letter'))}")
            
            if app.get('optimized_resume') and not resume_app:
                resume_app = app
                print(f"✅ Found application with optimized_resume: {app.get('application_id')}")
            
            if app.get('cover_letter') and not cover_letter_app:
                cover_letter_app = app
                print(f"✅ Found application with cover_letter: {app.get('application_id')}")
            
            if resume_app and cover_letter_app:
                break
        
        # Step 3: Test resume download
        resume_success = False
        if resume_app:
            resume_success = self.test_resume_download(resume_app['application_id'])
        else:
            print("⚠️  No application with optimized_resume found")
        
        # Step 4: Test cover letter download
        cover_letter_success = False
        if cover_letter_app:
            cover_letter_success = self.test_cover_letter_download(cover_letter_app['application_id'])
        else:
            print("⚠️  No application with cover_letter found")
        
        # If no applications with required fields, create test data
        if not resume_app and not cover_letter_app:
            print("📝 Creating test application with resume and cover letter...")
            return self.create_test_application_and_test_downloads()
        
        return resume_success or cover_letter_success

    def create_test_application_and_test_downloads(self):
        """Create a test application with resume and cover letter, then test downloads"""
        print("\n🔧 Creating test application with optimized resume and cover letter...")
        
        # Create application with job description to trigger AI generation
        app_data = {
            "job_id": "download_test_job_456",
            "job_title": "Senior Data Analyst",
            "company": "Download Test Corp",
            "location": "Remote",
            "job_description": """We are seeking a Senior Data Analyst with expertise in Python, SQL, and data visualization. 
            The ideal candidate will have experience with ETL pipelines, business intelligence tools like Tableau, 
            and strong analytical skills. You will work with cross-functional teams to drive data-driven decisions."""
        }
        
        success, app = self.run_test("Create Test Application", "POST", "applications", 200, app_data)
        
        if not success or not app.get('application_id'):
            print("❌ Failed to create test application")
            return False
        
        app_id = app['application_id']
        print(f"✅ Created test application: {app_id}")
        
        # Check if the application has the required fields
        has_resume = bool(app.get('optimized_resume'))
        has_cover_letter = bool(app.get('cover_letter'))
        
        print(f"   Has optimized_resume: {has_resume}")
        print(f"   Has cover_letter: {has_cover_letter}")
        
        # Test downloads
        resume_success = False
        cover_letter_success = False
        
        if has_resume:
            resume_success = self.test_resume_download(app_id)
        else:
            print("⚠️  No optimized_resume in created application")
        
        if has_cover_letter:
            cover_letter_success = self.test_cover_letter_download(app_id)
        else:
            print("⚠️  No cover_letter in created application")
        
        return resume_success or cover_letter_success

    def test_resume_download(self, application_id):
        """Test resume download endpoint"""
        print(f"\n📄 Testing Resume Download for application: {application_id}")
        
        url = f"{self.base_url}/api/applications/{application_id}/download/resume"
        headers = {
            'Authorization': f'Bearer {self.session_token}'
        }
        
        self.tests_run += 1
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            # Check status code
            if response.status_code != 200:
                print(f"❌ FAILED - Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    'name': 'Resume Download',
                    'expected': 200,
                    'actual': response.status_code,
                    'response': response.text[:200]
                })
                return False
            
            # Check Content-Type header
            content_type = response.headers.get('Content-Type', '')
            expected_content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            
            if content_type != expected_content_type:
                print(f"❌ FAILED - Wrong Content-Type")
                print(f"   Expected: {expected_content_type}")
                print(f"   Got: {content_type}")
                self.failed_tests.append({
                    'name': 'Resume Download Content-Type',
                    'error': f'Wrong Content-Type: {content_type}'
                })
                return False
            
            # Check Content-Disposition header
            content_disposition = response.headers.get('Content-Disposition', '')
            if not content_disposition.startswith('attachment; filename=Resume_'):
                print(f"❌ FAILED - Wrong Content-Disposition")
                print(f"   Expected: attachment; filename=Resume_*.docx")
                print(f"   Got: {content_disposition}")
                self.failed_tests.append({
                    'name': 'Resume Download Content-Disposition',
                    'error': f'Wrong Content-Disposition: {content_disposition}'
                })
                return False
            
            # Check if file is valid DOCX (check file signature)
            content = response.content
            if len(content) < 4:
                print(f"❌ FAILED - File too small: {len(content)} bytes")
                self.failed_tests.append({
                    'name': 'Resume Download File Size',
                    'error': f'File too small: {len(content)} bytes'
                })
                return False
            
            # DOCX files are ZIP files, so they should start with PK signature
            if not content.startswith(b'PK'):
                print(f"❌ FAILED - Invalid DOCX file signature")
                print(f"   Expected: PK (ZIP signature)")
                print(f"   Got: {content[:4]}")
                self.failed_tests.append({
                    'name': 'Resume Download File Signature',
                    'error': 'Invalid DOCX file signature'
                })
                return False
            
            # Success
            self.tests_passed += 1
            print(f"✅ PASSED - Resume Download")
            print(f"   ✅ Status: 200 OK")
            print(f"   ✅ Content-Type: {content_type}")
            print(f"   ✅ Content-Disposition: {content_disposition}")
            print(f"   ✅ File size: {len(content)} bytes")
            print(f"   ✅ Valid DOCX signature: PK")
            
            return True
            
        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timed out after 30s")
            self.failed_tests.append({'name': 'Resume Download', 'error': 'Timeout'})
            return False
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.failed_tests.append({'name': 'Resume Download', 'error': str(e)})
            return False

    def test_cover_letter_download(self, application_id):
        """Test cover letter download endpoint"""
        print(f"\n📄 Testing Cover Letter Download for application: {application_id}")
        
        url = f"{self.base_url}/api/applications/{application_id}/download/cover-letter"
        headers = {
            'Authorization': f'Bearer {self.session_token}'
        }
        
        self.tests_run += 1
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            # Check status code
            if response.status_code != 200:
                print(f"❌ FAILED - Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    'name': 'Cover Letter Download',
                    'expected': 200,
                    'actual': response.status_code,
                    'response': response.text[:200]
                })
                return False
            
            # Check Content-Type header
            content_type = response.headers.get('Content-Type', '')
            expected_content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            
            if content_type != expected_content_type:
                print(f"❌ FAILED - Wrong Content-Type")
                print(f"   Expected: {expected_content_type}")
                print(f"   Got: {content_type}")
                self.failed_tests.append({
                    'name': 'Cover Letter Download Content-Type',
                    'error': f'Wrong Content-Type: {content_type}'
                })
                return False
            
            # Check Content-Disposition header
            content_disposition = response.headers.get('Content-Disposition', '')
            if not content_disposition.startswith('attachment; filename=Cover_Letter_'):
                print(f"❌ FAILED - Wrong Content-Disposition")
                print(f"   Expected: attachment; filename=Cover_Letter_*.docx")
                print(f"   Got: {content_disposition}")
                self.failed_tests.append({
                    'name': 'Cover Letter Download Content-Disposition',
                    'error': f'Wrong Content-Disposition: {content_disposition}'
                })
                return False
            
            # Check if file is valid DOCX (check file signature)
            content = response.content
            if len(content) < 4:
                print(f"❌ FAILED - File too small: {len(content)} bytes")
                self.failed_tests.append({
                    'name': 'Cover Letter Download File Size',
                    'error': f'File too small: {len(content)} bytes'
                })
                return False
            
            # DOCX files are ZIP files, so they should start with PK signature
            if not content.startswith(b'PK'):
                print(f"❌ FAILED - Invalid DOCX file signature")
                print(f"   Expected: PK (ZIP signature)")
                print(f"   Got: {content[:4]}")
                self.failed_tests.append({
                    'name': 'Cover Letter Download File Signature',
                    'error': 'Invalid DOCX file signature'
                })
                return False
            
            # Success
            self.tests_passed += 1
            print(f"✅ PASSED - Cover Letter Download")
            print(f"   ✅ Status: 200 OK")
            print(f"   ✅ Content-Type: {content_type}")
            print(f"   ✅ Content-Disposition: {content_disposition}")
            print(f"   ✅ File size: {len(content)} bytes")
            print(f"   ✅ Valid DOCX signature: PK")
            
            return True
            
        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timed out after 30s")
            self.failed_tests.append({'name': 'Cover Letter Download', 'error': 'Timeout'})
            return False
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.failed_tests.append({'name': 'Cover Letter Download', 'error': str(e)})
            return False

    def run_download_tests(self):
        """Run download tests only"""
        print("🚀 Starting Download Endpoint Tests")
        print(f"📍 Base URL: {self.base_url}")
        print(f"🔑 Session Token: {self.session_token[:20]}...")
        
        start_time = datetime.now()
        
        # Test download endpoints
        download_success = self.test_download_endpoints()
        
        # Print summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "="*60)
        print("📊 DOWNLOAD TEST SUMMARY")
        print("="*60)
        print(f"✅ Tests passed: {self.tests_passed}/{self.tests_run}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        
        if download_success:
            print(f"   ✅ Download Endpoints: WORKING")
        else:
            print(f"   ❌ Download Endpoints: FAILED")
        
        if self.failed_tests:
            print(f"\n❌ Failed tests ({len(self.failed_tests)}):")
            for test in self.failed_tests:
                if 'error' in test:
                    print(f"   • {test['name']}: {test['error']}")
                else:
                    print(f"   • {test['name']}: Expected {test['expected']}, got {test['actual']}")
        
        print(f"\n🎯 Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")

if __name__ == "__main__":
    tester = DownloadTester()
    tester.run_download_tests()