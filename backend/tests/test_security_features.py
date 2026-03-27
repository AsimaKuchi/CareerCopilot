"""
Test Security Features for MyCareerCoPilot
- Security Headers Middleware (7 headers)
- Admin Role System (admin-only endpoints)
- CSRF Protection (token generation and validation)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from review request
TEST_USER = {"email": "test@demo.com", "password": "Test1234!"}
ADMIN_USER = {"email": "fuzailbukhari@gmail.com", "password": "Admin1234!"}


class TestSecurityHeaders:
    """Test that all 7 security headers are present on API responses."""
    
    def test_health_endpoint_returns_all_security_headers(self):
        """GET /api/health should return all 7 security headers."""
        response = requests.get(f"{BASE_URL}/api/health")
        
        # Status check
        assert response.status_code == 200, f"Health endpoint failed: {response.text}"
        
        # Check all 7 security headers
        headers = response.headers
        
        # 1. X-Frame-Options
        assert "X-Frame-Options" in headers, "Missing X-Frame-Options header"
        assert headers["X-Frame-Options"] == "DENY", f"X-Frame-Options should be DENY, got {headers['X-Frame-Options']}"
        
        # 2. X-Content-Type-Options
        assert "X-Content-Type-Options" in headers, "Missing X-Content-Type-Options header"
        assert headers["X-Content-Type-Options"] == "nosniff", f"X-Content-Type-Options should be nosniff"
        
        # 3. Referrer-Policy
        assert "Referrer-Policy" in headers, "Missing Referrer-Policy header"
        assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        
        # 4. Permissions-Policy
        assert "Permissions-Policy" in headers, "Missing Permissions-Policy header"
        assert "camera=()" in headers["Permissions-Policy"]
        assert "microphone=()" in headers["Permissions-Policy"]
        assert "geolocation=()" in headers["Permissions-Policy"]
        
        # 5. X-XSS-Protection
        assert "X-XSS-Protection" in headers, "Missing X-XSS-Protection header"
        assert headers["X-XSS-Protection"] == "1; mode=block"
        
        # 6. Strict-Transport-Security (HSTS)
        assert "Strict-Transport-Security" in headers, "Missing Strict-Transport-Security header"
        assert "max-age=31536000" in headers["Strict-Transport-Security"]
        assert "includeSubDomains" in headers["Strict-Transport-Security"]
        
        # 7. Content-Security-Policy
        assert "Content-Security-Policy" in headers, "Missing Content-Security-Policy header"
        csp = headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp
        
        print("✅ All 7 security headers present and correct")


class TestCSRFProtection:
    """Test CSRF token generation and validation."""
    
    def test_login_returns_csrf_token_in_body(self):
        """POST /api/auth/login should return csrf_token in response body."""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_USER
        )
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "csrf_token" in data, "csrf_token not in login response body"
        assert isinstance(data["csrf_token"], str), "csrf_token should be a string"
        assert len(data["csrf_token"]) > 20, "csrf_token seems too short"
        
        print(f"✅ Login returns csrf_token in body: {data['csrf_token'][:20]}...")
    
    def test_login_sets_csrf_cookie(self):
        """POST /api/auth/login should set csrf_token cookie."""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_USER
        )
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        # Check cookies
        cookies = session.cookies.get_dict()
        assert "csrf_token" in cookies, f"csrf_token cookie not set. Cookies: {cookies.keys()}"
        
        print(f"✅ Login sets csrf_token cookie: {cookies['csrf_token'][:20]}...")
    
    def test_csrf_token_matches_body_and_cookie(self):
        """CSRF token in body should match the cookie."""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_USER
        )
        
        assert response.status_code == 200
        
        body_token = response.json().get("csrf_token")
        cookie_token = session.cookies.get("csrf_token")
        
        assert body_token == cookie_token, f"Token mismatch: body={body_token[:20]}... cookie={cookie_token[:20]}..."
        
        print("✅ CSRF token in body matches cookie")


class TestAdminRoleSystem:
    """Test admin-only endpoints with role-based access control."""
    
    @pytest.fixture
    def regular_user_session(self):
        """Login as regular user and return session."""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_USER
        )
        if response.status_code != 200:
            pytest.skip(f"Regular user login failed: {response.text}")
        return session
    
    @pytest.fixture
    def admin_user_session(self):
        """Login as admin user and return session."""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json=ADMIN_USER
        )
        if response.status_code != 200:
            pytest.skip(f"Admin user login failed: {response.text}")
        return session
    
    def test_admin_stats_returns_403_for_regular_user(self, regular_user_session):
        """GET /api/admin/stats with regular user should return 403."""
        response = regular_user_session.get(f"{BASE_URL}/api/admin/stats")
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "Admin access required" in data.get("detail", ""), f"Expected 'Admin access required' in detail, got: {data}"
        
        print("✅ Regular user gets 403 on admin/stats")
    
    def test_admin_stats_returns_data_for_admin_user(self, admin_user_session):
        """GET /api/admin/stats with admin user should return stats object."""
        response = admin_user_session.get(f"{BASE_URL}/api/admin/stats")
        
        assert response.status_code == 200, f"Admin stats failed: {response.text}"
        
        data = response.json()
        
        # Verify stats fields
        assert "total_users" in data, "Missing total_users in stats"
        assert "total_jobs_indexed" in data, "Missing total_jobs_indexed in stats"
        assert "total_applications" in data, "Missing total_applications in stats"
        assert "active_sessions" in data, "Missing active_sessions in stats"
        assert "signups_last_7_days" in data, "Missing signups_last_7_days in stats"
        
        # Verify types
        assert isinstance(data["total_users"], int)
        assert isinstance(data["total_jobs_indexed"], int)
        
        print(f"✅ Admin stats returned: {data}")
    
    def test_admin_users_returns_403_for_regular_user(self, regular_user_session):
        """GET /api/admin/users with regular user should return 403."""
        response = regular_user_session.get(f"{BASE_URL}/api/admin/users")
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        
        print("✅ Regular user gets 403 on admin/users")
    
    def test_admin_users_returns_paginated_list_for_admin(self, admin_user_session):
        """GET /api/admin/users with admin should return paginated user list."""
        response = admin_user_session.get(f"{BASE_URL}/api/admin/users")
        
        assert response.status_code == 200, f"Admin users failed: {response.text}"
        
        data = response.json()
        
        # Verify pagination fields
        assert "users" in data, "Missing users array"
        assert "total" in data, "Missing total count"
        assert "page" in data, "Missing page number"
        assert "pages" in data, "Missing pages count"
        
        # Verify users array
        assert isinstance(data["users"], list)
        
        # Verify password_hash is NOT exposed
        if len(data["users"]) > 0:
            user = data["users"][0]
            assert "password_hash" not in user, "password_hash should not be exposed!"
            assert "reset_token" not in user, "reset_token should not be exposed!"
            assert "verification_token" not in user, "verification_token should not be exposed!"
        
        print(f"✅ Admin users returned {len(data['users'])} users (total: {data['total']})")
    
    def test_admin_unlock_user_returns_403_for_regular_user(self, regular_user_session):
        """POST /api/admin/unlock-user with regular user should return 403."""
        response = regular_user_session.post(
            f"{BASE_URL}/api/admin/unlock-user",
            json={"email": "test@example.com"}
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        
        print("✅ Regular user gets 403 on admin/unlock-user")
    
    def test_admin_unlock_user_works_for_admin(self, admin_user_session):
        """POST /api/admin/unlock-user with admin should unlock account."""
        # Try to unlock a non-existent user first to test 404
        response = admin_user_session.post(
            f"{BASE_URL}/api/admin/unlock-user",
            json={"email": "nonexistent@example.com"}
        )
        
        assert response.status_code == 404, f"Expected 404 for non-existent user, got {response.status_code}"
        
        # Now try to unlock the test user (should succeed even if not locked)
        response = admin_user_session.post(
            f"{BASE_URL}/api/admin/unlock-user",
            json={"email": TEST_USER["email"]}
        )
        
        assert response.status_code == 200, f"Unlock failed: {response.text}"
        
        data = response.json()
        assert "unlocked" in data.get("message", "").lower(), f"Expected unlock confirmation, got: {data}"
        
        print(f"✅ Admin unlock-user works: {data}")


class TestUnauthenticatedAccess:
    """Test that admin endpoints require authentication."""
    
    def test_admin_stats_returns_401_without_auth(self):
        """GET /api/admin/stats without auth should return 401."""
        response = requests.get(f"{BASE_URL}/api/admin/stats")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        print("✅ Unauthenticated request to admin/stats returns 401")
    
    def test_admin_users_returns_401_without_auth(self):
        """GET /api/admin/users without auth should return 401."""
        response = requests.get(f"{BASE_URL}/api/admin/users")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        print("✅ Unauthenticated request to admin/users returns 401")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
