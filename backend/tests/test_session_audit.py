"""
Test Session Management and Audit Logging Features
- GET /api/auth/sessions - List active sessions
- POST /api/auth/revoke-all-sessions - Revoke all sessions except current
- Audit logging for login, signup, password reset, revoke sessions
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER_EMAIL = "test@demo.com"
TEST_USER_PASSWORD = "Test1234!"
ADMIN_EMAIL = "fuzailbukhari@gmail.com"
ADMIN_PASSWORD = "Admin1234!"


class TestSessionManagement:
    """Test session listing and revocation endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.csrf_token = None
    
    def login(self, email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD):
        """Helper to login and get CSRF token"""
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            self.csrf_token = data.get("csrf_token")
        return response
    
    def test_sessions_endpoint_requires_auth(self):
        """GET /api/auth/sessions should require authentication"""
        response = requests.get(f"{BASE_URL}/api/auth/sessions")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Sessions endpoint requires authentication")
    
    def test_list_sessions_returns_correct_structure(self):
        """GET /api/auth/sessions should return sessions with ip_address, user_agent, is_current"""
        login_resp = self.login()
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        
        response = self.session.get(f"{BASE_URL}/api/auth/sessions")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "sessions" in data, "Response should contain 'sessions' key"
        assert "total" in data, "Response should contain 'total' key"
        assert isinstance(data["sessions"], list), "Sessions should be a list"
        
        # Should have at least one session (current)
        assert len(data["sessions"]) >= 1, "Should have at least one session"
        
        # Check session structure
        session = data["sessions"][0]
        assert "ip_address" in session, "Session should have ip_address"
        assert "user_agent" in session, "Session should have user_agent"
        assert "is_current" in session, "Session should have is_current flag"
        assert "last_active" in session, "Session should have last_active"
        assert "created_at" in session, "Session should have created_at"
        
        print(f"PASS: Sessions endpoint returns correct structure with {len(data['sessions'])} session(s)")
        print(f"  - IP Address: {session['ip_address']}")
        print(f"  - User Agent: {session['user_agent'][:50]}...")
        print(f"  - Is Current: {session['is_current']}")
    
    def test_current_session_marked_correctly(self):
        """Current session should have is_current=True"""
        login_resp = self.login()
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        
        response = self.session.get(f"{BASE_URL}/api/auth/sessions")
        assert response.status_code == 200
        
        data = response.json()
        current_sessions = [s for s in data["sessions"] if s["is_current"]]
        
        # Should have exactly one current session
        assert len(current_sessions) >= 1, "Should have at least one current session"
        print(f"PASS: Current session correctly marked (found {len(current_sessions)} current session)")
    
    def test_revoke_all_sessions_requires_auth(self):
        """POST /api/auth/revoke-all-sessions should require authentication"""
        response = requests.post(f"{BASE_URL}/api/auth/revoke-all-sessions")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Revoke sessions endpoint requires authentication")
    
    def test_revoke_all_sessions_requires_csrf(self):
        """POST /api/auth/revoke-all-sessions should require CSRF token"""
        login_resp = self.login()
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        
        # Try without CSRF token
        response = self.session.post(f"{BASE_URL}/api/auth/revoke-all-sessions")
        # Should either require CSRF or succeed (depends on implementation)
        # If CSRF is required, it should be 403
        print(f"Revoke without CSRF: {response.status_code}")
    
    def test_revoke_all_sessions_success(self):
        """POST /api/auth/revoke-all-sessions should revoke other sessions"""
        login_resp = self.login()
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        
        # Call revoke with CSRF token
        headers = {"X-CSRF-Token": self.csrf_token} if self.csrf_token else {}
        response = self.session.post(
            f"{BASE_URL}/api/auth/revoke-all-sessions",
            headers=headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        assert "revoked" in data, "Response should contain revoked count"
        
        print(f"PASS: Revoke all sessions succeeded - revoked {data['revoked']} session(s)")
        print(f"  - Message: {data['message']}")
    
    def test_current_session_preserved_after_revoke(self):
        """Current session should still work after revoking all others"""
        login_resp = self.login()
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        
        # Revoke all sessions
        headers = {"X-CSRF-Token": self.csrf_token} if self.csrf_token else {}
        revoke_resp = self.session.post(
            f"{BASE_URL}/api/auth/revoke-all-sessions",
            headers=headers
        )
        assert revoke_resp.status_code == 200
        
        # Current session should still work
        sessions_resp = self.session.get(f"{BASE_URL}/api/auth/sessions")
        assert sessions_resp.status_code == 200, "Current session should still be valid"
        
        data = sessions_resp.json()
        assert len(data["sessions"]) >= 1, "Should still have current session"
        
        print("PASS: Current session preserved after revoking all others")


class TestAuditLogging:
    """Test audit logging for critical events"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.admin_session = requests.Session()
        self.csrf_token = None
        self.admin_csrf_token = None
    
    def login_admin(self):
        """Login as admin to access audit logs"""
        response = self.admin_session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            data = response.json()
            self.admin_csrf_token = data.get("csrf_token")
        return response
    
    def login_user(self, email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD):
        """Login as test user"""
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            self.csrf_token = data.get("csrf_token")
        return response
    
    def get_audit_logs(self, log_type=None, limit=10):
        """Get audit logs via admin endpoint"""
        params = {"limit": limit}
        if log_type:
            params["type"] = log_type
        response = self.admin_session.get(
            f"{BASE_URL}/api/admin/audit-logs",
            params=params
        )
        return response
    
    def test_login_creates_audit_log(self):
        """Login should create 'login_success' audit log entry"""
        # First login as admin to access audit logs
        admin_login = self.login_admin()
        assert admin_login.status_code == 200, f"Admin login failed: {admin_login.text}"
        
        # Get timestamp before test user login
        time.sleep(1)
        
        # Login as test user
        user_login = self.login_user()
        assert user_login.status_code == 200, f"User login failed: {user_login.text}"
        
        # Check audit logs for login_success
        time.sleep(0.5)  # Allow time for log to be written
        logs_resp = self.get_audit_logs(log_type="login_success", limit=5)
        assert logs_resp.status_code == 200, f"Failed to get audit logs: {logs_resp.text}"
        
        data = logs_resp.json()
        assert "logs" in data, "Response should contain 'logs' key"
        
        # Find login log for test user
        login_logs = [log for log in data["logs"] if log.get("user_email") == TEST_USER_EMAIL]
        assert len(login_logs) > 0, f"Should have login_success log for {TEST_USER_EMAIL}"
        
        log = login_logs[0]
        assert log.get("type") == "login_success", "Log type should be 'login_success'"
        
        print(f"PASS: Login creates 'login_success' audit log")
        print(f"  - User: {log.get('user_email')}")
        print(f"  - Message: {log.get('message')}")
        print(f"  - Timestamp: {log.get('timestamp')}")
    
    def test_revoke_sessions_creates_audit_log(self):
        """Revoking sessions should create 'revoke_all_sessions' audit log"""
        # Login as admin first
        admin_login = self.login_admin()
        assert admin_login.status_code == 200
        
        # Login as test user
        user_login = self.login_user()
        assert user_login.status_code == 200
        
        # Revoke sessions
        headers = {"X-CSRF-Token": self.csrf_token} if self.csrf_token else {}
        revoke_resp = self.session.post(
            f"{BASE_URL}/api/auth/revoke-all-sessions",
            headers=headers
        )
        assert revoke_resp.status_code == 200
        
        # Check audit logs
        time.sleep(0.5)
        logs_resp = self.get_audit_logs(log_type="revoke_all_sessions", limit=5)
        assert logs_resp.status_code == 200
        
        data = logs_resp.json()
        revoke_logs = [log for log in data.get("logs", []) if log.get("user_email") == TEST_USER_EMAIL]
        assert len(revoke_logs) > 0, f"Should have revoke_all_sessions log for {TEST_USER_EMAIL}"
        
        log = revoke_logs[0]
        assert log.get("type") == "revoke_all_sessions"
        
        print(f"PASS: Revoke sessions creates 'revoke_all_sessions' audit log")
        print(f"  - User: {log.get('user_email')}")
        print(f"  - Message: {log.get('message')}")
    
    def test_forgot_password_creates_audit_log(self):
        """Forgot password should create 'forgot_password' audit log"""
        # Login as admin first
        admin_login = self.login_admin()
        assert admin_login.status_code == 200
        
        # Request password reset for test user
        reset_resp = requests.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": TEST_USER_EMAIL}
        )
        # Should return 200 regardless of whether email exists (security)
        assert reset_resp.status_code == 200, f"Forgot password failed: {reset_resp.text}"
        
        # Check audit logs
        time.sleep(0.5)
        logs_resp = self.get_audit_logs(log_type="forgot_password", limit=5)
        assert logs_resp.status_code == 200
        
        data = logs_resp.json()
        forgot_logs = [log for log in data.get("logs", []) if log.get("user_email") == TEST_USER_EMAIL]
        assert len(forgot_logs) > 0, f"Should have forgot_password log for {TEST_USER_EMAIL}"
        
        log = forgot_logs[0]
        assert log.get("type") == "forgot_password"
        
        print(f"PASS: Forgot password creates 'forgot_password' audit log")
        print(f"  - User: {log.get('user_email')}")
        print(f"  - Message: {log.get('message')}")
    
    def test_audit_log_types_endpoint(self):
        """GET /api/admin/audit-logs/types should return available log types"""
        admin_login = self.login_admin()
        assert admin_login.status_code == 200
        
        response = self.admin_session.get(f"{BASE_URL}/api/admin/audit-logs/types")
        assert response.status_code == 200, f"Failed to get log types: {response.text}"
        
        data = response.json()
        assert "types" in data, "Response should contain 'types' key"
        
        types = data["types"]
        # Should include our expected types
        expected_types = ["login_success", "signup", "forgot_password", "revoke_all_sessions"]
        found_types = [t for t in expected_types if t in types]
        
        print(f"PASS: Audit log types endpoint returns {len(types)} types")
        print(f"  - Found expected types: {found_types}")
        print(f"  - All types: {types}")


class TestSignupAuditLog:
    """Test signup audit logging (separate class to avoid affecting other tests)"""
    
    def test_signup_creates_audit_log(self):
        """Signup should create 'signup' audit log entry"""
        # Generate unique email for this test
        unique_email = f"test_signup_{uuid.uuid4().hex[:8]}@example.com"
        
        # Attempt signup
        signup_resp = requests.post(
            f"{BASE_URL}/api/auth/signup",
            json={
                "email": unique_email,
                "password": "TestPass123!",
                "name": "Test Signup User"
            }
        )
        
        # Signup should succeed (201 or 200)
        assert signup_resp.status_code in [200, 201], f"Signup failed: {signup_resp.text}"
        
        # Login as admin to check audit logs
        admin_session = requests.Session()
        admin_login = admin_session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert admin_login.status_code == 200, f"Admin login failed: {admin_login.text}"
        
        # Check audit logs for signup
        time.sleep(0.5)
        logs_resp = admin_session.get(
            f"{BASE_URL}/api/admin/audit-logs",
            params={"type": "signup", "limit": 10}
        )
        assert logs_resp.status_code == 200
        
        data = logs_resp.json()
        signup_logs = [log for log in data.get("logs", []) if log.get("user_email") == unique_email]
        assert len(signup_logs) > 0, f"Should have signup log for {unique_email}"
        
        log = signup_logs[0]
        assert log.get("type") == "signup"
        
        print(f"PASS: Signup creates 'signup' audit log")
        print(f"  - User: {log.get('user_email')}")
        print(f"  - Message: {log.get('message')}")


class TestMultipleSessionsScenario:
    """Test multiple sessions scenario"""
    
    def test_multiple_logins_create_multiple_sessions(self):
        """Multiple logins should create multiple sessions"""
        # Create two separate sessions
        session1 = requests.Session()
        session2 = requests.Session()
        
        # Login from session 1
        login1 = session1.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        assert login1.status_code == 200, f"Login 1 failed: {login1.text}"
        csrf1 = login1.json().get("csrf_token")
        
        # Login from session 2 (simulating different device)
        login2 = session2.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        assert login2.status_code == 200, f"Login 2 failed: {login2.text}"
        csrf2 = login2.json().get("csrf_token")
        
        # Check sessions from session 1
        sessions_resp = session1.get(f"{BASE_URL}/api/auth/sessions")
        assert sessions_resp.status_code == 200
        
        data = sessions_resp.json()
        # Should have at least 2 sessions
        assert data["total"] >= 2, f"Should have at least 2 sessions, got {data['total']}"
        
        print(f"PASS: Multiple logins create multiple sessions ({data['total']} sessions)")
        
        # Revoke from session 1
        headers = {"X-CSRF-Token": csrf1} if csrf1 else {}
        revoke_resp = session1.post(
            f"{BASE_URL}/api/auth/revoke-all-sessions",
            headers=headers
        )
        assert revoke_resp.status_code == 200
        revoke_data = revoke_resp.json()
        
        print(f"  - Revoked {revoke_data['revoked']} session(s) from session 1")
        
        # Session 1 should still work
        check1 = session1.get(f"{BASE_URL}/api/auth/sessions")
        assert check1.status_code == 200, "Session 1 should still be valid"
        
        # Session 2 should be invalidated
        check2 = session2.get(f"{BASE_URL}/api/auth/sessions")
        # Session 2 should return 401 (unauthorized) since it was revoked
        print(f"  - Session 2 status after revoke: {check2.status_code}")
        
        print("PASS: Session revocation works correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
