"""
Test suite for 'What to Do Next' feature endpoints.
Tests the next-steps API for tracking post-application actions and AI content generation.

Endpoints tested:
- GET /api/applications/{id}/next-steps - Get next steps data with progress
- PUT /api/applications/{id}/next-steps - Update step completion status  
- POST /api/applications/{id}/next-steps/generate - Generate AI content for steps
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data prefix for cleanup
TEST_PREFIX = "NEXTSTEPS_TEST_"


class TestSetup:
    """Helper class for test setup and data management."""
    
    @staticmethod
    def create_test_user_and_session(session):
        """Create a test user and session, return user_id and session_token."""
        import pymongo
        
        client = pymongo.MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
        db = client[os.environ.get('DB_NAME', 'test_database')]
        
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        session_token = f"test_session_{uuid.uuid4().hex[:16]}"
        
        # Create user
        db.users.insert_one({
            "user_id": user_id,
            "email": f"{TEST_PREFIX}user_{uuid.uuid4().hex[:6]}@test.com",
            "name": f"{TEST_PREFIX}Test User",
            "created_at": datetime.utcnow().isoformat()
        })
        
        # Create session
        from datetime import timedelta
        db.user_sessions.insert_one({
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "created_at": datetime.utcnow().isoformat()
        })
        
        # Create profile
        db.user_profiles.insert_one({
            "user_id": user_id,
            "skills": [{"name": "Python", "years": "3-5"}, {"name": "React", "years": "1-2"}],
            "experience_years": 5,
            "job_titles": ["Software Engineer"],
            "email": f"{TEST_PREFIX}user@test.com",
            "phone_number": "555-123-4567",
            "linkedin_url": "https://linkedin.com/in/testuser"
        })
        
        client.close()
        return user_id, session_token
    
    @staticmethod
    def create_test_application(session, user_id, session_token, status="applied"):
        """Create a test application, return application_id."""
        import pymongo
        
        client = pymongo.MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
        db = client[os.environ.get('DB_NAME', 'test_database')]
        
        app_id = f"app_{uuid.uuid4().hex[:12]}"
        
        db.applications.insert_one({
            "application_id": app_id,
            "user_id": user_id,
            "job_id": f"job_{uuid.uuid4().hex[:8]}",
            "job_title": f"{TEST_PREFIX}Software Engineer",
            "company": f"{TEST_PREFIX}Tech Corp",
            "location": "Remote",
            "job_description": "We are looking for a skilled software engineer to join our team.",
            "status": status,
            "match_score": 85,
            "created_at": datetime.utcnow().isoformat()
        })
        
        client.close()
        return app_id
    
    @staticmethod
    def cleanup_test_data():
        """Clean up all test data."""
        import pymongo
        
        client = pymongo.MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
        db = client[os.environ.get('DB_NAME', 'test_database')]
        
        db.users.delete_many({"name": {"$regex": f"^{TEST_PREFIX}"}})
        db.users.delete_many({"email": {"$regex": f"^{TEST_PREFIX}"}})
        db.user_sessions.delete_many({"session_token": {"$regex": "^test_session_"}})
        db.user_profiles.delete_many({"email": {"$regex": f"^{TEST_PREFIX}"}})
        db.applications.delete_many({"job_title": {"$regex": f"^{TEST_PREFIX}"}})
        
        client.close()


@pytest.fixture(scope="class")
def test_env():
    """Set up test environment and clean up after."""
    TestSetup.cleanup_test_data()
    yield
    TestSetup.cleanup_test_data()


@pytest.fixture
def api_session():
    """Create a requests session."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def authenticated_client(api_session, test_env):
    """Create an authenticated session with test user."""
    user_id, session_token = TestSetup.create_test_user_and_session(api_session)
    api_session.cookies.set("session_token", session_token)
    api_session.user_id = user_id
    api_session.session_token = session_token
    return api_session


class TestGetNextSteps:
    """Tests for GET /api/applications/{id}/next-steps endpoint."""
    
    def test_get_next_steps_returns_default_structure(self, authenticated_client):
        """Verify GET endpoint returns default next steps structure."""
        app_id = TestSetup.create_test_application(
            authenticated_client, 
            authenticated_client.user_id, 
            authenticated_client.session_token,
            status="applied"
        )
        
        response = authenticated_client.get(f"{BASE_URL}/api/applications/{app_id}/next-steps")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify structure
        assert "application_id" in data
        assert "next_steps" in data
        assert "progress" in data
        
        # Verify all 6 steps are present
        next_steps = data["next_steps"]
        expected_steps = ["follow_company", "find_recruiter", "send_message", 
                         "prep_interview", "track_outcome", "follow_up"]
        for step_id in expected_steps:
            assert step_id in next_steps, f"Missing step: {step_id}"
            assert "completed" in next_steps[step_id]
            assert "title" in next_steps[step_id]
            assert "description" in next_steps[step_id]
        
        # Verify progress structure
        progress = data["progress"]
        assert "completed" in progress
        assert "total" in progress
        assert "percentage" in progress
        assert progress["total"] == 6
        assert progress["completed"] == 0  # Initially no steps completed
        assert progress["percentage"] == 0
        
        print(f"✅ GET next-steps returns correct structure with {len(next_steps)} steps")
    
    def test_get_next_steps_requires_auth(self, api_session):
        """Verify GET endpoint requires authentication."""
        response = api_session.get(f"{BASE_URL}/api/applications/fake_app_id/next-steps")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ GET next-steps requires authentication")
    
    def test_get_next_steps_404_for_nonexistent_app(self, authenticated_client):
        """Verify GET endpoint returns 404 for non-existent application."""
        response = authenticated_client.get(f"{BASE_URL}/api/applications/nonexistent_app_123/next-steps")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✅ GET next-steps returns 404 for non-existent app")


class TestUpdateNextSteps:
    """Tests for PUT /api/applications/{id}/next-steps endpoint."""
    
    def test_update_step_completion_status(self, authenticated_client):
        """Verify PUT endpoint updates step completion status."""
        app_id = TestSetup.create_test_application(
            authenticated_client, 
            authenticated_client.user_id, 
            authenticated_client.session_token
        )
        
        # Mark follow_company as completed
        response = authenticated_client.put(
            f"{BASE_URL}/api/applications/{app_id}/next-steps",
            json={"step_id": "follow_company", "completed": True}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["success"] == True
        assert data["next_steps"]["follow_company"]["completed"] == True
        assert data["progress"]["completed"] == 1
        assert data["progress"]["percentage"] == round((1/6) * 100)
        
        print(f"✅ PUT updates step completion - progress now {data['progress']['percentage']}%")
    
    def test_update_multiple_steps_progress(self, authenticated_client):
        """Verify progress updates correctly when multiple steps are completed."""
        app_id = TestSetup.create_test_application(
            authenticated_client, 
            authenticated_client.user_id, 
            authenticated_client.session_token
        )
        
        # Complete 3 steps
        steps_to_complete = ["follow_company", "find_recruiter", "send_message"]
        
        for step_id in steps_to_complete:
            response = authenticated_client.put(
                f"{BASE_URL}/api/applications/{app_id}/next-steps",
                json={"step_id": step_id, "completed": True}
            )
            assert response.status_code == 200
        
        # Verify final progress
        data = response.json()
        assert data["progress"]["completed"] == 3
        assert data["progress"]["percentage"] == 50  # 3/6 = 50%
        
        print("✅ Multiple steps completion updates progress correctly (50%)")
    
    def test_update_track_outcome_status(self, authenticated_client):
        """Verify track_outcome step can be updated with outcome value."""
        app_id = TestSetup.create_test_application(
            authenticated_client, 
            authenticated_client.user_id, 
            authenticated_client.session_token
        )
        
        # Update outcome to interview_scheduled
        response = authenticated_client.put(
            f"{BASE_URL}/api/applications/{app_id}/next-steps",
            json={
                "step_id": "track_outcome", 
                "outcome": "interview_scheduled",
                "completed": True
            }
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["next_steps"]["track_outcome"]["outcome"] == "interview_scheduled"
        assert data["next_steps"]["track_outcome"]["completed"] == True
        
        print("✅ Track outcome step updated with outcome value")
    
    def test_update_follow_up_reminder(self, authenticated_client):
        """Verify follow_up step can set reminder_date."""
        app_id = TestSetup.create_test_application(
            authenticated_client, 
            authenticated_client.user_id, 
            authenticated_client.session_token
        )
        
        reminder_date = "2025-01-20"
        
        response = authenticated_client.put(
            f"{BASE_URL}/api/applications/{app_id}/next-steps",
            json={
                "step_id": "follow_up", 
                "reminder_date": reminder_date,
                "completed": True
            }
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["next_steps"]["follow_up"]["reminder_date"] == reminder_date
        assert data["next_steps"]["follow_up"]["completed"] == True
        
        print(f"✅ Follow-up reminder set for {reminder_date}")
    
    def test_update_invalid_step_id_returns_400(self, authenticated_client):
        """Verify PUT returns 400 for invalid step_id."""
        app_id = TestSetup.create_test_application(
            authenticated_client, 
            authenticated_client.user_id, 
            authenticated_client.session_token
        )
        
        response = authenticated_client.put(
            f"{BASE_URL}/api/applications/{app_id}/next-steps",
            json={"step_id": "invalid_step", "completed": True}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✅ Invalid step_id returns 400")


class TestGenerateNextStepContent:
    """Tests for POST /api/applications/{id}/next-steps/generate endpoint."""
    
    def test_generate_outreach_message(self, authenticated_client):
        """Verify AI generates outreach message for send_message step."""
        app_id = TestSetup.create_test_application(
            authenticated_client, 
            authenticated_client.user_id, 
            authenticated_client.session_token
        )
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/applications/{app_id}/next-steps/generate",
            json={"step_id": "send_message", "content_type": "linkedin_message"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["success"] == True
        assert data["step_id"] == "send_message"
        assert "generated_content" in data
        assert len(data["generated_content"]) > 50  # Should have meaningful content
        
        print(f"✅ Generated outreach message ({len(data['generated_content'])} chars)")
        print(f"   Preview: {data['generated_content'][:100]}...")
    
    def test_generate_interview_questions(self, authenticated_client):
        """Verify AI generates interview questions for prep_interview step."""
        app_id = TestSetup.create_test_application(
            authenticated_client, 
            authenticated_client.user_id, 
            authenticated_client.session_token
        )
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/applications/{app_id}/next-steps/generate",
            json={"step_id": "prep_interview"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["success"] == True
        assert data["step_id"] == "prep_interview"
        assert "generated_questions" in data
        assert len(data["generated_questions"]) > 100  # Should have multiple Q&A pairs
        
        # Verify format includes questions
        assert "Q1" in data["generated_questions"] or "question" in data["generated_questions"].lower()
        
        print(f"✅ Generated interview questions ({len(data['generated_questions'])} chars)")
        print(f"   Preview: {data['generated_questions'][:150]}...")
    
    def test_generate_email_message(self, authenticated_client):
        """Verify AI generates email message variant."""
        app_id = TestSetup.create_test_application(
            authenticated_client, 
            authenticated_client.user_id, 
            authenticated_client.session_token
        )
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/applications/{app_id}/next-steps/generate",
            json={"step_id": "send_message", "content_type": "email"}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "generated_content" in data
        # Email should have subject line
        assert "Subject:" in data["generated_content"] or len(data["generated_content"]) > 50
        
        print(f"✅ Generated email message")
    
    def test_generate_connection_request(self, authenticated_client):
        """Verify AI generates LinkedIn connection request."""
        app_id = TestSetup.create_test_application(
            authenticated_client, 
            authenticated_client.user_id, 
            authenticated_client.session_token
        )
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/applications/{app_id}/next-steps/generate",
            json={"step_id": "send_message", "content_type": "connection_request"}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "generated_content" in data
        # Connection request should be short (under 300 chars for LinkedIn limit)
        assert len(data["generated_content"]) < 400
        
        print(f"✅ Generated connection request ({len(data['generated_content'])} chars)")
    
    def test_generate_invalid_step_returns_400(self, authenticated_client):
        """Verify generate returns 400 for invalid steps."""
        app_id = TestSetup.create_test_application(
            authenticated_client, 
            authenticated_client.user_id, 
            authenticated_client.session_token
        )
        
        # Try to generate content for follow_company (not supported)
        response = authenticated_client.post(
            f"{BASE_URL}/api/applications/{app_id}/next-steps/generate",
            json={"step_id": "follow_company"}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✅ Generate returns 400 for unsupported step")
    
    def test_generated_content_persists(self, authenticated_client):
        """Verify generated content is saved and returned in GET."""
        app_id = TestSetup.create_test_application(
            authenticated_client, 
            authenticated_client.user_id, 
            authenticated_client.session_token
        )
        
        # Generate content
        gen_response = authenticated_client.post(
            f"{BASE_URL}/api/applications/{app_id}/next-steps/generate",
            json={"step_id": "send_message", "content_type": "linkedin_message"}
        )
        assert gen_response.status_code == 200
        generated = gen_response.json()["generated_content"]
        
        # Verify it persists in GET
        get_response = authenticated_client.get(f"{BASE_URL}/api/applications/{app_id}/next-steps")
        assert get_response.status_code == 200
        
        data = get_response.json()
        assert data["next_steps"]["send_message"]["generated_content"] == generated
        
        print("✅ Generated content persists in database")


class TestNextStepsIntegration:
    """Integration tests for the complete next-steps workflow."""
    
    def test_full_workflow(self, authenticated_client):
        """Test complete workflow: create app → get steps → update → generate → verify."""
        # Create application
        app_id = TestSetup.create_test_application(
            authenticated_client, 
            authenticated_client.user_id, 
            authenticated_client.session_token
        )
        
        # 1. Get initial steps
        response = authenticated_client.get(f"{BASE_URL}/api/applications/{app_id}/next-steps")
        assert response.status_code == 200
        assert response.json()["progress"]["percentage"] == 0
        print("  1. Initial steps retrieved (0% progress)")
        
        # 2. Complete first step
        response = authenticated_client.put(
            f"{BASE_URL}/api/applications/{app_id}/next-steps",
            json={"step_id": "follow_company", "completed": True}
        )
        assert response.status_code == 200
        print("  2. Completed 'follow_company' step")
        
        # 3. Generate message
        response = authenticated_client.post(
            f"{BASE_URL}/api/applications/{app_id}/next-steps/generate",
            json={"step_id": "send_message", "content_type": "linkedin_message"}
        )
        assert response.status_code == 200
        print("  3. Generated outreach message")
        
        # 4. Complete send_message step
        response = authenticated_client.put(
            f"{BASE_URL}/api/applications/{app_id}/next-steps",
            json={"step_id": "send_message", "completed": True}
        )
        assert response.status_code == 200
        print("  4. Completed 'send_message' step")
        
        # 5. Generate interview questions
        response = authenticated_client.post(
            f"{BASE_URL}/api/applications/{app_id}/next-steps/generate",
            json={"step_id": "prep_interview"}
        )
        assert response.status_code == 200
        print("  5. Generated interview questions")
        
        # 6. Update outcome
        response = authenticated_client.put(
            f"{BASE_URL}/api/applications/{app_id}/next-steps",
            json={"step_id": "track_outcome", "outcome": "interview_scheduled", "completed": True}
        )
        assert response.status_code == 200
        print("  6. Updated outcome to 'interview_scheduled'")
        
        # 7. Verify final state
        response = authenticated_client.get(f"{BASE_URL}/api/applications/{app_id}/next-steps")
        assert response.status_code == 200
        
        data = response.json()
        assert data["progress"]["completed"] == 3  # 3 steps completed
        assert data["progress"]["percentage"] == 50
        assert data["next_steps"]["send_message"]["generated_content"] is not None
        assert data["next_steps"]["prep_interview"]["generated_questions"] is not None
        assert data["next_steps"]["track_outcome"]["outcome"] == "interview_scheduled"
        
        print(f"  7. Final state verified: {data['progress']['percentage']}% complete")
        print("✅ Full workflow test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
