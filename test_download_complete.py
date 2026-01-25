#!/usr/bin/env python3

import requests
import sys
import json

def test_download_with_data():
    """Test download endpoints by creating application with resume and cover letter data"""
    base_url = "https://jobmatchpro-15.preview.emergentagent.com"
    session_token = "test_session_1768797070346"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session_token}'
    }
    
    print("🚀 Testing Download Endpoints with Resume and Cover Letter Data")
    print("="*60)
    
    # Create application with optimized_resume and cover_letter
    app_data = {
        "job_id": "download_test_job_789",
        "job_title": "Senior Data Analyst",
        "company": "Download Test Corp",
        "location": "Remote",
        "job_description": "We are seeking a Senior Data Analyst with expertise in Python, SQL, and data visualization.",
        "optimized_resume": """JOHN DOE
Senior Data Analyst
Email: john.doe@email.com | Phone: (555) 123-4567

PROFESSIONAL SUMMARY
Experienced Data Analyst with 6+ years of expertise in SQL, Python, and business intelligence. 
Proven track record of building ETL pipelines, creating executive dashboards, and driving data-driven decisions.

TECHNICAL SKILLS
• Programming: Python, SQL, R, JavaScript
• Databases: PostgreSQL, MySQL, MongoDB, Snowflake
• Visualization: Tableau, Power BI, Matplotlib, Seaborn
• Cloud: AWS (S3, Redshift, Lambda), Azure
• Tools: Git, Docker, Airflow, dbt

WORK EXPERIENCE

Senior Data Analyst | TechCorp Inc. | 2020 - Present
• Built automated ETL pipelines processing 10M+ records daily using Python and SQL
• Created executive dashboards in Tableau reducing reporting time by 75%
• Collaborated with product teams to define KPIs and track business metrics
• Implemented A/B testing framework increasing conversion rates by 12%

Data Analyst | StartupXYZ | 2018 - 2020
• Analyzed customer behavior data using SQL and Python to identify retention patterns
• Developed predictive models improving customer lifetime value predictions by 25%
• Built real-time monitoring dashboards for key business metrics
• Worked with cross-functional teams to translate business requirements into technical solutions

EDUCATION
Bachelor of Science in Statistics | University of Technology | 2017""",
        "cover_letter": """Dear Hiring Manager,

I am writing to express my strong interest in the Senior Data Analyst position at Download Test Corp. With over 6 years of experience in data analysis, SQL, and Python, I am excited about the opportunity to contribute to your team's data-driven initiatives.

In my current role as Senior Data Analyst at TechCorp Inc., I have successfully:
• Built automated ETL pipelines processing over 10 million records daily
• Created executive dashboards in Tableau that reduced reporting time by 75%
• Implemented A/B testing frameworks that increased conversion rates by 12%
• Collaborated with cross-functional teams to define and track key business metrics

My technical expertise includes Python, SQL, Tableau, and cloud platforms like AWS and Azure. I have experience with data warehousing, ETL processes, and business intelligence tools that align perfectly with your requirements.

I am particularly drawn to Download Test Corp's commitment to data-driven decision making and would welcome the opportunity to discuss how my analytical skills and experience can contribute to your team's success.

Thank you for your consideration. I look forward to hearing from you.

Sincerely,
John Doe"""
    }
    
    print("\n🔧 Creating application with resume and cover letter data...")
    
    try:
        # Create application
        create_url = f"{base_url}/api/applications"
        response = requests.post(create_url, json=app_data, headers=headers, timeout=30)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ Failed to create application: {response.text[:200]}")
            return False
        
        app_response = response.json()
        app_id = app_response.get('application_id')
        
        print(f"   ✅ Created application: {app_id}")
        print(f"   Has optimized_resume: {bool(app_response.get('optimized_resume'))}")
        print(f"   Has cover_letter: {bool(app_response.get('cover_letter'))}")
        
        if not app_response.get('optimized_resume'):
            print("   ❌ No optimized_resume in response")
            return False
        
        if not app_response.get('cover_letter'):
            print("   ❌ No cover_letter in response")
            return False
        
        # Test resume download
        print(f"\n📄 Testing Resume Download for {app_id}...")
        resume_success = test_resume_download(base_url, session_token, app_id)
        
        # Test cover letter download
        print(f"\n📄 Testing Cover Letter Download for {app_id}...")
        cover_success = test_cover_letter_download(base_url, session_token, app_id)
        
        return resume_success and cover_success
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_resume_download(base_url, session_token, app_id):
    """Test resume download endpoint"""
    headers = {'Authorization': f'Bearer {session_token}'}
    url = f"{base_url}/api/applications/{app_id}/download/resume"
    
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ Failed: {response.text[:200]}")
            return False
        
        # Check headers
        content_type = response.headers.get('Content-Type', '')
        content_disposition = response.headers.get('Content-Disposition', '')
        
        print(f"   Content-Type: {content_type}")
        print(f"   Content-Disposition: {content_disposition}")
        
        # Validate Content-Type
        expected_content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        if content_type != expected_content_type:
            print(f"   ❌ Wrong Content-Type. Expected: {expected_content_type}")
            return False
        
        # Validate Content-Disposition
        if not content_disposition.startswith('attachment; filename=Resume_'):
            print(f"   ❌ Wrong Content-Disposition. Expected: attachment; filename=Resume_*.docx")
            return False
        
        # Check file content
        content = response.content
        print(f"   File size: {len(content)} bytes")
        
        if len(content) < 4:
            print(f"   ❌ File too small")
            return False
        
        # Check DOCX signature (ZIP format starts with PK)
        if not content.startswith(b'PK'):
            print(f"   ❌ Invalid DOCX signature. Got: {content[:4]}")
            return False
        
        print(f"   ✅ Resume download successful!")
        print(f"   ✅ Valid DOCX file with PK signature")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_cover_letter_download(base_url, session_token, app_id):
    """Test cover letter download endpoint"""
    headers = {'Authorization': f'Bearer {session_token}'}
    url = f"{base_url}/api/applications/{app_id}/download/cover-letter"
    
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ Failed: {response.text[:200]}")
            return False
        
        # Check headers
        content_type = response.headers.get('Content-Type', '')
        content_disposition = response.headers.get('Content-Disposition', '')
        
        print(f"   Content-Type: {content_type}")
        print(f"   Content-Disposition: {content_disposition}")
        
        # Validate Content-Type
        expected_content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        if content_type != expected_content_type:
            print(f"   ❌ Wrong Content-Type. Expected: {expected_content_type}")
            return False
        
        # Validate Content-Disposition
        if not content_disposition.startswith('attachment; filename=Cover_Letter_'):
            print(f"   ❌ Wrong Content-Disposition. Expected: attachment; filename=Cover_Letter_*.docx")
            return False
        
        # Check file content
        content = response.content
        print(f"   File size: {len(content)} bytes")
        
        if len(content) < 4:
            print(f"   ❌ File too small")
            return False
        
        # Check DOCX signature (ZIP format starts with PK)
        if not content.startswith(b'PK'):
            print(f"   ❌ Invalid DOCX signature. Got: {content[:4]}")
            return False
        
        print(f"   ✅ Cover letter download successful!")
        print(f"   ✅ Valid DOCX file with PK signature")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_download_with_data()
    
    print("\n" + "="*60)
    print("📊 DOWNLOAD TEST RESULTS")
    print("="*60)
    
    if success:
        print("✅ ALL DOWNLOAD TESTS PASSED")
        print("   ✅ Resume download endpoint working correctly")
        print("   ✅ Cover letter download endpoint working correctly")
        print("   ✅ Correct Content-Type headers")
        print("   ✅ Correct Content-Disposition headers")
        print("   ✅ Valid DOCX file signatures")
    else:
        print("❌ DOWNLOAD TESTS FAILED")
        print("   Check the error messages above for details")
    
    sys.exit(0 if success else 1)