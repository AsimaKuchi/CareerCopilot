"""
API tests for Profile v2 Schema Migration endpoints.
Tests GET/PUT /api/profile and GET /api/autofill/data endpoints.
"""

import pytest
import requests
import os
from datetime import datetime, timezone, timedelta

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test session token - created by mongosh setup
TEST_SESSION_TOKEN = None
TEST_USER_ID = None


def setup_module(module):
    """Create test user and session before running tests."""
    global TEST_SESSION_TOKEN, TEST_USER_ID
    
    import subprocess
    import re
    
    # Create test user via mongosh
    result = subprocess.run([
        'mongosh', '--eval', '''
use('test_database');
var userId = 'test-api-profile-v2-' + Date.now();
var sessionToken = 'test_api_session_v2_' + Date.now();
db.users.insertOne({
  user_id: userId,
  email: 'test.api.v2.' + Date.now() + '@example.com',
  name: 'API Test User',
  picture: 'https://via.placeholder.com/150',
  created_at: new Date()
});
db.user_sessions.insertOne({
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000),
  created_at: new Date()
});
db.user_profiles.insertOne({
  user_id: userId,
  profile_version: 1,
  resume_text: 'Test resume text for API testing',
  skills: [
    {name: 'Python', years: '3-5'},
    {name: 'JavaScript', years: '1-2'},
    'SQL'
  ],
  experience_years: 5,
  job_titles: ['Software Engineer'],
  preferred_locations: ['Toronto'],
  salary_min: 80000,
  salary_max: 120000,
  job_type: ['full-time'],
  work_authorization: 'canadian_citizen',
  seniority_level: 'senior',
  email: 'test.api.v2@example.com',
  phone_number: '4165551234',
  linkedin_url: 'https://linkedin.com/in/testuser',
  highest_education: 'bachelor',
  address_city: 'Toronto',
  address_state: 'Ontario',
  address_country: 'Canada',
  updated_at: new Date()
});
print('SESSION_TOKEN=' + sessionToken);
print('USER_ID=' + userId);
'''
    ], capture_output=True, text=True)
    
    # Parse output for session token and user ID
    output = result.stdout
    for line in output.split('\n'):
        if line.startswith('SESSION_TOKEN='):
            TEST_SESSION_TOKEN = line.split('=')[1].strip()
        elif line.startswith('USER_ID='):
            TEST_USER_ID = line.split('=')[1].strip()
    
    if not TEST_SESSION_TOKEN:
        pytest.skip("Failed to create test session")


def teardown_module(module):
    """Clean up test data after tests."""
    if TEST_USER_ID:
        import subprocess
        subprocess.run([
            'mongosh', '--eval', f'''
use('test_database');
db.users.deleteMany({{user_id: /test-api-profile-v2-/}});
db.user_sessions.deleteMany({{session_token: /test_api_session_v2_/}});
db.user_profiles.deleteMany({{user_id: /test-api-profile-v2-/}});
'''
        ], capture_output=True)


@pytest.fixture
def api_client():
    """Shared requests session."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def auth_headers():
    """Get authorization headers with test session token."""
    return {"Authorization": f"Bearer {TEST_SESSION_TOKEN}"}


class TestProfileEndpointAuth:
    """Test authentication requirements for profile endpoints."""
    
    def test_get_profile_requires_auth(self, api_client):
        """GET /api/profile should return 401 without auth."""
        response = api_client.get(f"{BASE_URL}/api/profile")
        assert response.status_code == 401
        assert "Not authenticated" in response.json().get("detail", "")
    
    def test_put_profile_requires_auth(self, api_client):
        """PUT /api/profile should return 401 without auth."""
        response = api_client.put(
            f"{BASE_URL}/api/profile",
            json={"skills": ["Python"]}
        )
        assert response.status_code == 401
        assert "Not authenticated" in response.json().get("detail", "")
    
    def test_autofill_data_requires_auth(self, api_client):
        """GET /api/autofill/data should return 401 without auth."""
        response = api_client.get(f"{BASE_URL}/api/autofill/data")
        assert response.status_code == 401
        assert "Not authenticated" in response.json().get("detail", "")


class TestGetProfile:
    """Test GET /api/profile endpoint with v2 schema."""
    
    def test_get_profile_returns_v2_schema(self, api_client, auth_headers):
        """GET /api/profile should return profile with v2 schema."""
        response = api_client.get(
            f"{BASE_URL}/api/profile",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check v2 schema fields
        assert data.get("profile_version") == 2
        assert "migrated_at" in data
        assert "structured" in data
    
    def test_get_profile_has_structured_work_authorization(self, api_client, auth_headers):
        """GET /api/profile should have structured workAuthorization."""
        response = api_client.get(
            f"{BASE_URL}/api/profile",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        structured = data.get("structured", {})
        work_auth = structured.get("workAuthorization", {})
        
        # Check work authorization structure
        assert "raw" in work_auth
        assert "normalized" in work_auth
        
        normalized = work_auth.get("normalized", {})
        assert "status" in normalized
        assert "requiresSponsorship" in normalized
        assert "country" in normalized
    
    def test_get_profile_has_structured_skills(self, api_client, auth_headers):
        """GET /api/profile should have structured skills with numeric years."""
        response = api_client.get(
            f"{BASE_URL}/api/profile",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        structured = data.get("structured", {})
        skills = structured.get("skills", {})
        
        # Check skills structure
        assert "items" in skills
        items = skills.get("items", [])
        
        # Should have skills from test data
        assert len(items) >= 1
        
        # Each skill should have name and years (numeric)
        for skill in items:
            assert "name" in skill
            assert "years" in skill
    
    def test_get_profile_preserves_original_fields(self, api_client, auth_headers):
        """GET /api/profile should preserve original v1 fields."""
        response = api_client.get(
            f"{BASE_URL}/api/profile",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Original fields should be preserved
        assert "user_id" in data
        assert "work_authorization" in data  # Original string field
        assert "phone_number" in data  # Original string field
        assert "skills" in data  # Original skills array
    
    def test_get_profile_has_contact_with_e164_phone(self, api_client, auth_headers):
        """GET /api/profile should have contact with E.164 phone."""
        response = api_client.get(
            f"{BASE_URL}/api/profile",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        structured = data.get("structured", {})
        contact = structured.get("contact", {})
        phone = contact.get("phone", {})
        
        # Check phone normalization
        assert "normalized" in phone
        normalized_phone = phone.get("normalized")
        
        # E.164 format starts with +
        if normalized_phone:
            assert normalized_phone.startswith("+")


class TestPutProfile:
    """Test PUT /api/profile endpoint with v2 schema regeneration."""
    
    def test_put_profile_updates_and_returns_v2(self, api_client, auth_headers):
        """PUT /api/profile should update and return v2 schema."""
        response = api_client.put(
            f"{BASE_URL}/api/profile",
            headers=auth_headers,
            json={"experience_years": 6}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return v2 schema
        assert data.get("profile_version") == 2
        assert "structured" in data
        
        # Should have updated value
        assert data.get("experience_years") == 6
    
    def test_put_profile_regenerates_structured_data(self, api_client, auth_headers):
        """PUT /api/profile should regenerate structured data."""
        # Update work authorization
        response = api_client.put(
            f"{BASE_URL}/api/profile",
            headers=auth_headers,
            json={"work_authorization": "permanent_resident"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structured data was regenerated
        structured = data.get("structured", {})
        work_auth = structured.get("workAuthorization", {})
        normalized = work_auth.get("normalized", {})
        
        assert normalized.get("status") == "permanent_resident"
        assert normalized.get("requiresSponsorship") == False
    
    def test_put_profile_updates_skills_with_years(self, api_client, auth_headers):
        """PUT /api/profile should handle skills with bucket years."""
        new_skills = [
            {"name": "Python", "years": "5+"},
            {"name": "React", "years": "3-5"},
            "Docker"  # String skill without years
        ]
        
        response = api_client.put(
            f"{BASE_URL}/api/profile",
            headers=auth_headers,
            json={"skills": new_skills}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check skills in response
        skills = data.get("skills", [])
        assert len(skills) == 3
        
        # Check structured skills have numeric years
        structured = data.get("structured", {})
        skill_items = structured.get("skills", {}).get("items", [])
        
        # Python should have years converted from "5+" to numeric
        python_skill = next((s for s in skill_items if s.get("name") == "Python"), None)
        assert python_skill is not None
        assert python_skill.get("years") == 7  # "5+" converts to 7
    
    def test_put_profile_updates_phone_normalization(self, api_client, auth_headers):
        """PUT /api/profile should normalize phone to E.164."""
        response = api_client.put(
            f"{BASE_URL}/api/profile",
            headers=auth_headers,
            json={"phone_number": "(647) 555-9876"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structured phone
        structured = data.get("structured", {})
        contact = structured.get("contact", {})
        phone = contact.get("phone", {})
        
        assert phone.get("normalized") == "+16475559876"
        assert phone.get("formatted") == "+1 (647) 555-9876"


class TestAutofillData:
    """Test GET /api/autofill/data endpoint."""
    
    def test_autofill_returns_normalized_data(self, api_client, auth_headers):
        """GET /api/autofill/data should return normalized data."""
        response = api_client.get(
            f"{BASE_URL}/api/autofill/data",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "firstName" in data
        assert "lastName" in data
        assert "email" in data
        assert "phone" in data
        assert "skills" in data
    
    def test_autofill_phone_is_e164(self, api_client, auth_headers):
        """GET /api/autofill/data should return E.164 phone."""
        response = api_client.get(
            f"{BASE_URL}/api/autofill/data",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        phone = data.get("phone", "")
        if phone:
            # E.164 format starts with +
            assert phone.startswith("+")
            # Should have country code + number
            assert len(phone) >= 10
    
    def test_autofill_has_work_authorization_status(self, api_client, auth_headers):
        """GET /api/autofill/data should have normalized work authorization."""
        response = api_client.get(
            f"{BASE_URL}/api/autofill/data",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have work authorization fields
        assert "workAuthorization" in data
        assert "requiresSponsorship" in data
    
    def test_autofill_has_skills_list(self, api_client, auth_headers):
        """GET /api/autofill/data should have skills as list of names."""
        response = api_client.get(
            f"{BASE_URL}/api/autofill/data",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        skills = data.get("skills", [])
        assert isinstance(skills, list)
        
        # Skills should be strings (names only)
        for skill in skills:
            assert isinstance(skill, str)
    
    def test_autofill_has_location_fields(self, api_client, auth_headers):
        """GET /api/autofill/data should have normalized location."""
        response = api_client.get(
            f"{BASE_URL}/api/autofill/data",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have location fields
        assert "city" in data
        assert "state" in data
        assert "country" in data
    
    def test_autofill_has_professional_fields(self, api_client, auth_headers):
        """GET /api/autofill/data should have professional fields."""
        response = api_client.get(
            f"{BASE_URL}/api/autofill/data",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have professional fields
        assert "education" in data
        assert "seniorityLevel" in data
        assert "willingToRelocate" in data
        assert "noticePeriod" in data


class TestProfileMigration:
    """Test profile migration from v1 to v2 format."""
    
    def test_v1_profile_auto_migrates_on_get(self, api_client, auth_headers):
        """v1 profile should auto-migrate to v2 on GET."""
        # First GET should trigger migration
        response = api_client.get(
            f"{BASE_URL}/api/profile",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be v2 now
        assert data.get("profile_version") == 2
        assert "structured" in data
        assert "migrated_at" in data
    
    def test_migration_preserves_original_work_auth(self, api_client, auth_headers):
        """Migration should preserve original work_authorization string."""
        response = api_client.get(
            f"{BASE_URL}/api/profile",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Original field preserved
        assert "work_authorization" in data
        
        # Structured version also exists
        structured = data.get("structured", {})
        work_auth = structured.get("workAuthorization", {})
        assert "raw" in work_auth
        assert "normalized" in work_auth


class TestWorkAuthorizationNormalization:
    """Test work authorization normalization via API."""
    
    def test_canadian_citizen_no_sponsorship(self, api_client, auth_headers):
        """canadian_citizen should have requiresSponsorship=false."""
        # Update to canadian_citizen
        response = api_client.put(
            f"{BASE_URL}/api/profile",
            headers=auth_headers,
            json={"work_authorization": "canadian_citizen"}
        )
        
        assert response.status_code == 200
        
        # Check autofill data
        autofill_response = api_client.get(
            f"{BASE_URL}/api/autofill/data",
            headers=auth_headers
        )
        
        assert autofill_response.status_code == 200
        data = autofill_response.json()
        
        assert data.get("workAuthorization") == "citizen"
        assert data.get("requiresSponsorship") == False
    
    def test_pgwp_requires_sponsorship(self, api_client, auth_headers):
        """pgwp should have requiresSponsorship=true."""
        # Update to pgwp
        response = api_client.put(
            f"{BASE_URL}/api/profile",
            headers=auth_headers,
            json={"work_authorization": "pgwp"}
        )
        
        assert response.status_code == 200
        
        # Check autofill data
        autofill_response = api_client.get(
            f"{BASE_URL}/api/autofill/data",
            headers=auth_headers
        )
        
        assert autofill_response.status_code == 200
        data = autofill_response.json()
        
        assert data.get("workAuthorization") == "pgwp"
        assert data.get("requiresSponsorship") == True


class TestSkillsYearsConversion:
    """Test skills years bucket to numeric conversion."""
    
    def test_bucket_years_converted_to_numeric(self, api_client, auth_headers):
        """Bucket years like '3-5' should convert to numeric (4)."""
        # Update skills with bucket years
        response = api_client.put(
            f"{BASE_URL}/api/profile",
            headers=auth_headers,
            json={
                "skills": [
                    {"name": "Python", "years": "3-5"},
                    {"name": "JavaScript", "years": "<1"},
                    {"name": "React", "years": "5+"}
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structured skills
        structured = data.get("structured", {})
        skill_items = structured.get("skills", {}).get("items", [])
        
        # Find each skill and check years
        python_skill = next((s for s in skill_items if s.get("name") == "Python"), None)
        js_skill = next((s for s in skill_items if s.get("name") == "JavaScript"), None)
        react_skill = next((s for s in skill_items if s.get("name") == "React"), None)
        
        assert python_skill is not None
        assert python_skill.get("years") == 4  # "3-5" -> 4
        
        assert js_skill is not None
        assert js_skill.get("years") == 0.5  # "<1" -> 0.5
        
        assert react_skill is not None
        assert react_skill.get("years") == 7  # "5+" -> 7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
