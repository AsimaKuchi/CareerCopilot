#!/usr/bin/env python3

import requests
import json

def test_interview_prep():
    """Test interview prep endpoint specifically"""
    base_url = "https://autofill-browser.preview.emergentagent.com"
    session_token = "test_session_1768797070346"
    
    print("📋 TESTING INTERVIEW PREP GENERATION")
    print("="*50)
    
    url = f"{base_url}/api/ai/interview-prep"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session_token}'
    }
    
    prep_data = {
        "job_title": "Software Engineer",
        "company": "Google",
        "job_description": "We are looking for a skilled software engineer to join our team. You will work on large-scale distributed systems, write clean code, and collaborate with cross-functional teams."
    }
    
    print(f"🔍 Making request to: {url}")
    print(f"📋 Request data: {prep_data}")
    print()
    
    try:
        response = requests.post(url, json=prep_data, headers=headers, timeout=60)
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        data = response.json()
        prep_materials = data.get('prep_materials', '')
        
        if not prep_materials:
            print("❌ No prep_materials in response")
            return
        
        print(f"✅ Response received, content length: {len(prep_materials)} characters")
        print()
        
        # Check for required sections
        required_sections = [
            "1. COMMON INTERVIEW QUESTIONS",
            "2. BEHAVIORAL QUESTIONS", 
            "3. TECHNICAL QUESTIONS",
            "4. INTERVIEW TIPS",
            "5. QUESTIONS TO ASK THE INTERVIEWER"
        ]
        
        print("🔍 CHECKING REQUIRED SECTIONS:")
        for section in required_sections:
            found = section in prep_materials
            status = "✅" if found else "❌"
            print(f"{status} {section}")
        print()
        
        # Check formatting requirements
        print("🔍 CHECKING FORMATTING:")
        
        # Check for level-4 headers (####)
        has_level4_headers = "####" in prep_materials
        print(f"{'✅' if has_level4_headers else '❌'} Level-4 headers (####): {'Found' if has_level4_headers else 'Missing'}")
        
        # Check for blockquotes (>)
        has_blockquotes = ">" in prep_materials
        print(f"{'✅' if has_blockquotes else '❌'} Blockquotes (>): {'Found' if has_blockquotes else 'Missing'}")
        
        # Check for asterisks (should NOT be present)
        has_asterisks = "*" in prep_materials
        print(f"{'❌' if has_asterisks else '✅'} No asterisks (*): {'Found asterisks!' if has_asterisks else 'Clean'}")
        
        if has_asterisks:
            # Show where asterisks appear
            lines_with_asterisks = []
            for i, line in enumerate(prep_materials.split('\n'), 1):
                if '*' in line:
                    lines_with_asterisks.append(f"Line {i}: {line[:80]}...")
                    if len(lines_with_asterisks) >= 5:  # Show first 5 occurrences
                        break
            
            print("   Asterisk locations:")
            for line_info in lines_with_asterisks:
                print(f"     {line_info}")
        
        print()
        
        # Show sample content
        print("📄 SAMPLE CONTENT (first 10 lines):")
        lines = prep_materials.split('\n')[:10]
        for i, line in enumerate(lines, 1):
            if line.strip():
                print(f"  {i:2d}: {line[:80]}...")
        
        print()
        
        # Final assessment
        all_sections_present = all(section in prep_materials for section in required_sections)
        proper_formatting = has_level4_headers and has_blockquotes and not has_asterisks
        
        print("🏁 FINAL ASSESSMENT:")
        print(f"✅ All sections present: {'YES' if all_sections_present else 'NO'}")
        print(f"✅ Proper formatting: {'YES' if proper_formatting else 'NO'}")
        print(f"✅ Content length adequate: {'YES' if len(prep_materials) > 1000 else 'NO'}")
        
        if all_sections_present and proper_formatting and len(prep_materials) > 1000:
            print("🎉 SUCCESS: Interview prep generation working correctly!")
        else:
            print("❌ ISSUES FOUND: Interview prep needs formatting fixes")
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")

if __name__ == "__main__":
    test_interview_prep()