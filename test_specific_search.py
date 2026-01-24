#!/usr/bin/env python3

import requests
import json
import time

def test_specific_search():
    """Test the exact user reported search scenario with detailed analysis"""
    
    base_url = "https://jobsmart-8.preview.emergentagent.com"
    session_token = "test_session_1768797070346"
    
    url = f"{base_url}/api/jobs/greenhouse/search"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session_token}',
        'Accept': 'text/event-stream'
    }
    
    # Test the exact search scenario from review request
    search_data = {
        "query": "business analyst",
        "location": "greater toronto area, ontario"
    }
    
    print("🎯 TESTING EXACT USER SEARCH SCENARIO")
    print("="*60)
    print(f"Query: '{search_data['query']}'")
    print(f"Location: '{search_data['location']}'")
    print("Expected: Should extract keywords ['toronto', 'ontario'] and match jobs with those locations")
    print("Expected: Should find 30-50 analyst jobs (Data Analyst, Business Analyst, Risk Analyst, etc.)")
    print()
    
    jobs_received = []
    location_keywords_found = set()
    analyst_types_found = set()
    companies_found = set()
    
    try:
        response = requests.post(url, json=search_data, headers=headers, stream=True, timeout=70)
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        print("✅ Streaming response received")
        print("Processing jobs...")
        print()
        
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                data_str = line[6:]  # Remove 'data: ' prefix
                try:
                    data = json.loads(data_str)
                    
                    # Skip heartbeat/progress messages
                    if data.get('heartbeat') or data.get('progress'):
                        continue
                    
                    if data.get('done'):
                        total_jobs = data.get('total', 0)
                        print(f"✅ Search completed: {total_jobs} jobs found")
                        break
                    else:
                        jobs_received.append(data)
                        
                        # Analyze job details
                        title = data.get('title', '').lower()
                        company = data.get('company', '')
                        location = data.get('location', '').lower()
                        
                        # Track location keywords
                        if 'toronto' in location:
                            location_keywords_found.add('toronto')
                        if 'ontario' in location:
                            location_keywords_found.add('ontario')
                        if 'canada' in location:
                            location_keywords_found.add('canada')
                        
                        # Track analyst types
                        if 'analyst' in title:
                            if 'business' in title:
                                analyst_types_found.add('Business Analyst')
                            elif 'data' in title:
                                analyst_types_found.add('Data Analyst')
                            elif 'financial' in title or 'finance' in title:
                                analyst_types_found.add('Financial Analyst')
                            elif 'risk' in title:
                                analyst_types_found.add('Risk Analyst')
                            elif 'fraud' in title:
                                analyst_types_found.add('Fraud Analyst')
                            else:
                                analyst_types_found.add('Other Analyst')
                        
                        companies_found.add(company)
                        
                        # Show first 10 jobs with details
                        if len(jobs_received) <= 10:
                            print(f"Job {len(jobs_received)}: {data.get('title')} at {company}")
                            print(f"   Location: {data.get('location')}")
                            print(f"   Match Score: {data.get('match_score')}")
                            print(f"   Source: {data.get('source')}")
                            print()
                
                except json.JSONDecodeError:
                    continue
        
        # Analysis
        print("="*60)
        print("📊 SEARCH ANALYSIS")
        print("="*60)
        
        print(f"Total jobs found: {len(jobs_received)}")
        print(f"Location keywords matched: {list(location_keywords_found)}")
        print(f"Analyst types found: {list(analyst_types_found)}")
        print(f"Companies with jobs: {len(companies_found)}")
        print(f"Sample companies: {list(companies_found)[:5]}")
        
        print("\n📍 LOCATION MATCHING ANALYSIS:")
        if location_keywords_found:
            print(f"✅ Location matching IS working - found jobs with: {list(location_keywords_found)}")
        else:
            print("❌ Location matching NOT working - no jobs found with toronto/ontario/canada")
        
        print("\n🔍 QUERY MATCHING ANALYSIS:")
        if analyst_types_found:
            print(f"✅ Query matching IS working - found analyst types: {list(analyst_types_found)}")
        else:
            print("❌ Query matching NOT working - no analyst jobs found")
        
        print("\n🎯 EXPECTATION vs REALITY:")
        if len(jobs_received) >= 30:
            print(f"✅ MEETS EXPECTATION: Found {len(jobs_received)} jobs (≥30 expected)")
        elif len(jobs_received) >= 10:
            print(f"⚠️  PARTIAL: Found {len(jobs_received)} jobs (expected 30-50)")
        else:
            print(f"❌ BELOW EXPECTATION: Only {len(jobs_received)} jobs found (expected 30-50)")
        
        # Check if we're getting the expected companies
        expected_companies = ['stripe', 'coinbase', 'airbnb', 'dropbox']
        found_expected = [comp for comp in companies_found if any(exp.lower() in comp.lower() for exp in expected_companies)]
        
        if found_expected:
            print(f"✅ Found jobs from expected companies: {found_expected}")
        else:
            print(f"⚠️  No jobs found from expected companies: {expected_companies}")
        
        print("\n🔧 RECOMMENDATIONS:")
        if len(jobs_received) < 30:
            print("• Search should return more analyst jobs in Toronto area")
            print("• Check if location matching is too restrictive")
            print("• Verify if 'business analyst' query is matching related roles like 'Data Analyst'")
        
        if not location_keywords_found:
            print("• Location keyword extraction may not be working correctly")
            print("• 'greater toronto area, ontario' should extract ['toronto', 'ontario']")
        
        if not analyst_types_found:
            print("• Query matching may be too strict")
            print("• 'business analyst' should match various analyst roles")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_specific_search()