#!/usr/bin/env python3

import requests
import json
import time

class PriorityTester:
    def __init__(self):
        self.base_url = "https://job-auto-fill-1.preview.emergentagent.com"
        self.session_token = "test_session_1768797070346"
        
    def test_interview_prep(self):
        """Test Interview Prep generation endpoint"""
        print("🔍 Testing Interview Prep Generation (/api/ai/interview-prep)")
        print("="*60)
        
        url = f"{self.base_url}/api/ai/interview-prep"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.session_token}'
        }
        
        prep_data = {
            "job_title": "Software Engineer",
            "company": "Google",
            "job_description": "We are looking for a skilled software engineer to join our team. You will work on large-scale distributed systems, write clean code, and collaborate with cross-functional teams."
        }
        
        try:
            print(f"📤 Sending request to: {url}")
            print(f"📋 Data: {json.dumps(prep_data, indent=2)}")
            
            response = requests.post(url, json=prep_data, headers=headers, timeout=60)
            
            print(f"📥 Response Status: {response.status_code}")
            print(f"📥 Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                prep_materials = data.get('prep_materials', '')
                
                print(f"✅ SUCCESS - Interview Prep Generated")
                print(f"📄 Content Length: {len(prep_materials)} characters")
                
                # Check formatting
                required_sections = [
                    "1. COMMON INTERVIEW QUESTIONS",
                    "2. BEHAVIORAL QUESTIONS", 
                    "3. TECHNICAL QUESTIONS",
                    "4. INTERVIEW TIPS",
                    "5. QUESTIONS TO ASK THE INTERVIEWER"
                ]
                
                print(f"\n📋 Format Validation:")
                for section in required_sections:
                    if section in prep_materials:
                        print(f"   ✅ {section}")
                    else:
                        print(f"   ❌ {section}")
                
                has_headers = "####" in prep_materials
                has_blockquotes = ">" in prep_materials
                has_asterisks = "*" in prep_materials
                
                print(f"   ✅ Level-4 headers (####): {'Yes' if has_headers else 'No'}")
                print(f"   ✅ Blockquotes (>): {'Yes' if has_blockquotes else 'No'}")
                print(f"   ✅ No asterisks (*): {'Yes' if not has_asterisks else 'No'}")
                
                # Show sample
                print(f"\n📄 Sample Content (first 500 chars):")
                print(prep_materials[:500] + "...")
                
                return True
            else:
                print(f"❌ FAILED - Status: {response.status_code}")
                print(f"📄 Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return False
    
    def test_job_search(self):
        """Test Job Search streaming endpoint"""
        print("\n🔍 Testing Job Search Streaming (/api/jobs/search)")
        print("="*60)
        
        url = f"{self.base_url}/api/jobs/search"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.session_token}'
        }
        
        search_data = {
            "query": "engineer",
            "location": ""
        }
        
        try:
            print(f"📤 Sending request to: {url}")
            print(f"🔍 Query: '{search_data['query']}', Location: '{search_data['location']}'")
            
            start_time = time.time()
            response = requests.post(url, json=search_data, headers=headers, timeout=60)
            elapsed = time.time() - start_time
            
            print(f"📥 Response Status: {response.status_code}")
            print(f"⏱️  Response Time: {elapsed:.2f}s")
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get('jobs', [])
                total = data.get('total', 0)
                
                print(f"✅ SUCCESS - Job Search Completed")
                print(f"📊 Jobs Found: {len(jobs)}")
                print(f"📊 Total Reported: {total}")
                
                if len(jobs) > 0:
                    print(f"\n📋 Job Structure Validation:")
                    sample_job = jobs[0]
                    
                    required_fields = ['job_id', 'title', 'company', 'match_score', 'match_strengths', 'match_gaps']
                    for field in required_fields:
                        if field in sample_job:
                            print(f"   ✅ {field}: {sample_job.get(field)}")
                        else:
                            print(f"   ❌ {field}: Missing")
                    
                    print(f"\n📄 Sample Jobs:")
                    for i, job in enumerate(jobs[:3]):
                        title = job.get('title', 'N/A')
                        company = job.get('company', 'N/A')
                        score = job.get('match_score', 'N/A')
                        strengths = len(job.get('match_strengths', []))
                        gaps = len(job.get('match_gaps', []))
                        print(f"   {i+1}. {title} at {company}")
                        print(f"      Score: {score}, Strengths: {strengths}, Gaps: {gaps}")
                else:
                    print(f"⚠️  No jobs found - this may indicate filtering issues")
                
                return True
            else:
                print(f"❌ FAILED - Status: {response.status_code}")
                print(f"📄 Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return False

def main():
    tester = PriorityTester()
    
    print("🎯 PRIORITY ENDPOINT TESTING")
    print("Testing the two specific endpoints mentioned in review request")
    print("="*80)
    
    # Test both priority endpoints
    interview_success = tester.test_interview_prep()
    job_search_success = tester.test_job_search()
    
    print("\n" + "="*80)
    print("📊 PRIORITY TEST SUMMARY")
    print("="*80)
    
    print(f"📋 Interview Prep (/api/ai/interview-prep): {'✅ PASSED' if interview_success else '❌ FAILED'}")
    print(f"🔍 Job Search (/api/jobs/search): {'✅ PASSED' if job_search_success else '❌ FAILED'}")
    
    if interview_success and job_search_success:
        print(f"\n🎉 ALL PRIORITY TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  SOME PRIORITY TESTS FAILED - See details above")
        return 1

if __name__ == "__main__":
    exit(main())