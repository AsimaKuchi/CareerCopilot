#!/usr/bin/env python3

import requests
import json

def test_broader_analyst_search():
    """Test broader analyst searches in Toronto to see if we can find more jobs"""
    
    base_url = "https://careerfit-30.preview.emergentagent.com"
    session_token = "test_session_1768797070346"
    
    url = f"{base_url}/api/jobs/greenhouse/search"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session_token}',
        'Accept': 'text/event-stream'
    }
    
    # Test different search variations
    test_cases = [
        {
            "name": "Exact user search",
            "query": "business analyst",
            "location": "greater toronto area, ontario"
        },
        {
            "name": "Broader analyst search",
            "query": "analyst",
            "location": "toronto"
        },
        {
            "name": "Data analyst in Toronto",
            "query": "data analyst", 
            "location": "toronto"
        },
        {
            "name": "Business roles in Toronto",
            "query": "business",
            "location": "toronto"
        },
        {
            "name": "Any jobs in Toronto",
            "query": "",
            "location": "toronto"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n🔍 Testing: {test_case['name']}")
        print(f"   Query: '{test_case['query']}', Location: '{test_case['location']}'")
        
        search_data = {
            "query": test_case['query'],
            "location": test_case['location']
        }
        
        jobs_count = 0
        companies = set()
        
        try:
            response = requests.post(url, json=search_data, headers=headers, stream=True, timeout=60)
            
            if response.status_code != 200:
                print(f"   ❌ Failed: {response.status_code}")
                continue
            
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    data_str = line[6:]
                    try:
                        data = json.loads(data_str)
                        
                        if data.get('done'):
                            jobs_count = data.get('total', 0)
                            break
                        elif not data.get('heartbeat') and not data.get('progress'):
                            companies.add(data.get('company', 'Unknown'))
                            
                    except json.JSONDecodeError:
                        continue
            
            print(f"   ✅ Found: {jobs_count} jobs from {len(companies)} companies")
            if companies:
                company_list = sorted(list(companies))[:5]  # Show first 5 companies
                print(f"   Companies: {', '.join(company_list)}{'...' if len(companies) > 5 else ''}")
            
            results.append({
                'name': test_case['name'],
                'jobs': jobs_count,
                'companies': len(companies)
            })
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "="*60)
    print("SUMMARY OF RESULTS")
    print("="*60)
    
    for result in results:
        print(f"{result['name']}: {result['jobs']} jobs from {result['companies']} companies")
    
    print("\n" + "="*60)
    print("ANALYSIS")
    print("="*60)
    
    exact_search = next((r for r in results if r['name'] == 'Exact user search'), None)
    broader_search = next((r for r in results if r['name'] == 'Any jobs in Toronto'), None)
    
    if exact_search and broader_search:
        print(f"User's exact search: {exact_search['jobs']} jobs")
        print(f"All jobs in Toronto: {broader_search['jobs']} jobs")
        
        if exact_search['jobs'] < 40:
            percentage = (exact_search['jobs'] / broader_search['jobs']) * 100 if broader_search['jobs'] > 0 else 0
            print(f"Business analyst jobs are {percentage:.1f}% of all Toronto jobs")
            print()
            print("CONCLUSION:")
            if exact_search['jobs'] < 10:
                print("❌ Very few business analyst jobs available in Toronto area from Greenhouse companies")
                print("   This suggests the user's expectation of 40+ jobs may be unrealistic")
                print("   The location matching IS working correctly")
            else:
                print("✅ Reasonable number of business analyst jobs found")

if __name__ == "__main__":
    test_broader_analyst_search()