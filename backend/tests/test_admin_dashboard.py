"""
Admin Dashboard API Tests for MyCareerCopilot.
Tests: Overview stats, User management, Security monitoring, Audit logs, Support tools.
Requires admin authentication (fuzailbukhari@gmail.com / Admin1234!)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAdminAuth:
    """Test admin authentication and access control"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Login as admin and return session with CSRF token"""
        session = requests.Session()
        # Login as admin
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fuzailbukhari@gmail.com",
            "password": "Admin1234!"
        })
        assert login_resp.status_code == 200, f"Admin login failed: {login_resp.text}"
        data = login_resp.json()
        csrf_token = data.get("csrf_token")
        if csrf_token:
            session.headers.update({"X-CSRF-Token": csrf_token})
        return session
    
    @pytest.fixture(scope="class")
    def non_admin_session(self):
        """Login as non-admin user and return session"""
        session = requests.Session()
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@demo.com",
            "password": "Test1234!"
        })
        assert login_resp.status_code == 200, f"Non-admin login failed: {login_resp.text}"
        data = login_resp.json()
        csrf_token = data.get("csrf_token")
        if csrf_token:
            session.headers.update({"X-CSRF-Token": csrf_token})
        return session
    
    def test_admin_login_success(self, admin_session):
        """Verify admin can login and has admin role"""
        resp = admin_session.get(f"{BASE_URL}/api/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("role") == "admin", f"Expected admin role, got: {data.get('role')}"
        assert data.get("email") == "fuzailbukhari@gmail.com"
        print(f"Admin login verified: {data.get('email')} with role={data.get('role')}")
    
    def test_non_admin_gets_403_on_admin_endpoints(self, non_admin_session):
        """Non-admin user should get 403 on all admin endpoints"""
        endpoints = [
            "/api/admin/overview",
            "/api/admin/users",
            "/api/admin/security/summary",
            "/api/admin/audit-logs",
            "/api/admin/support/search?q=test",
        ]
        for endpoint in endpoints:
            resp = non_admin_session.get(f"{BASE_URL}{endpoint}")
            assert resp.status_code == 403, f"Expected 403 for {endpoint}, got {resp.status_code}"
            print(f"Non-admin correctly blocked from {endpoint} (403)")


class TestAdminOverview:
    """Test GET /api/admin/overview - Dashboard stats"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        session = requests.Session()
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fuzailbukhari@gmail.com",
            "password": "Admin1234!"
        })
        assert login_resp.status_code == 200
        data = login_resp.json()
        csrf_token = data.get("csrf_token")
        if csrf_token:
            session.headers.update({"X-CSRF-Token": csrf_token})
        return session
    
    def test_overview_returns_stats(self, admin_session):
        """GET /api/admin/overview returns dashboard stats"""
        resp = admin_session.get(f"{BASE_URL}/api/admin/overview")
        assert resp.status_code == 200, f"Overview failed: {resp.text}"
        data = resp.json()
        
        # Verify required fields exist
        required_fields = [
            "total_users", "free_users", "pro_users", "mrr",
            "active_users_24h", "apps_today", "failed_logins_24h",
            "locked_accounts", "signups_today", "signups_7d", "signups_30d",
            "total_jobs_indexed", "usage_this_month"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify data types
        assert isinstance(data["total_users"], int)
        assert isinstance(data["mrr"], (int, float))
        assert isinstance(data["usage_this_month"], dict)
        
        print(f"Overview stats: total_users={data['total_users']}, mrr=${data['mrr']}, pro_users={data['pro_users']}")


class TestAdminUserManagement:
    """Test user management endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        session = requests.Session()
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fuzailbukhari@gmail.com",
            "password": "Admin1234!"
        })
        assert login_resp.status_code == 200
        data = login_resp.json()
        csrf_token = data.get("csrf_token")
        if csrf_token:
            session.headers.update({"X-CSRF-Token": csrf_token})
        return session
    
    @pytest.fixture(scope="class")
    def test_user_id(self, admin_session):
        """Get test user's user_id for testing"""
        resp = admin_session.get(f"{BASE_URL}/api/admin/support/search?q=test@demo.com")
        assert resp.status_code == 200
        data = resp.json()
        users = data.get("users", [])
        assert len(users) > 0, "Test user not found"
        return users[0]["user_id"]
    
    def test_list_users_paginated(self, admin_session):
        """GET /api/admin/users returns paginated user list"""
        resp = admin_session.get(f"{BASE_URL}/api/admin/users?page=1&limit=10")
        assert resp.status_code == 200, f"List users failed: {resp.text}"
        data = resp.json()
        
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        assert isinstance(data["users"], list)
        
        print(f"Users list: {len(data['users'])} users on page {data['page']}/{data['pages']}, total={data['total']}")
    
    def test_list_users_with_search(self, admin_session):
        """GET /api/admin/users with search filter"""
        resp = admin_session.get(f"{BASE_URL}/api/admin/users?search=test")
        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data
        print(f"Search 'test' returned {len(data['users'])} users")
    
    def test_list_users_with_plan_filter(self, admin_session):
        """GET /api/admin/users with plan filter"""
        resp = admin_session.get(f"{BASE_URL}/api/admin/users?plan=free")
        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data
        print(f"Plan filter 'free' returned {len(data['users'])} users")
    
    def test_get_user_detail(self, admin_session, test_user_id):
        """GET /api/admin/users/{user_id} returns detailed user info"""
        resp = admin_session.get(f"{BASE_URL}/api/admin/users/{test_user_id}")
        assert resp.status_code == 200, f"Get user detail failed: {resp.text}"
        data = resp.json()
        
        # Verify structure
        assert "user" in data
        assert "profile" in data
        assert "usage" in data
        assert "app_count" in data
        assert "saved_jobs_count" in data
        assert "recent_activity" in data
        
        user = data["user"]
        assert user.get("email") == "test@demo.com"
        print(f"User detail: {user.get('email')}, apps={data['app_count']}, saved_jobs={data['saved_jobs_count']}")
    
    def test_ban_and_unban_user(self, admin_session, test_user_id):
        """POST /api/admin/users/{user_id}/ban and /unban work correctly"""
        # Ban user
        ban_resp = admin_session.post(
            f"{BASE_URL}/api/admin/users/{test_user_id}/ban",
            json={"reason": "Test ban from pytest"}
        )
        assert ban_resp.status_code == 200, f"Ban failed: {ban_resp.text}"
        ban_data = ban_resp.json()
        assert "banned" in ban_data.get("message", "").lower()
        print(f"Ban response: {ban_data.get('message')}")
        
        # Verify user is banned
        detail_resp = admin_session.get(f"{BASE_URL}/api/admin/users/{test_user_id}")
        assert detail_resp.status_code == 200
        assert detail_resp.json()["user"].get("banned") == True
        
        # Unban user
        unban_resp = admin_session.post(f"{BASE_URL}/api/admin/users/{test_user_id}/unban")
        assert unban_resp.status_code == 200, f"Unban failed: {unban_resp.text}"
        unban_data = unban_resp.json()
        assert "unbanned" in unban_data.get("message", "").lower()
        print(f"Unban response: {unban_data.get('message')}")
        
        # Verify user is unbanned
        detail_resp2 = admin_session.get(f"{BASE_URL}/api/admin/users/{test_user_id}")
        assert detail_resp2.status_code == 200
        assert detail_resp2.json()["user"].get("banned") == False
    
    def test_subscription_override(self, admin_session, test_user_id):
        """POST /api/admin/users/{user_id}/subscription overrides user plan"""
        # Set to pro
        pro_resp = admin_session.post(
            f"{BASE_URL}/api/admin/users/{test_user_id}/subscription",
            json={"plan": "pro"}
        )
        assert pro_resp.status_code == 200, f"Subscription override failed: {pro_resp.text}"
        pro_data = pro_resp.json()
        assert "pro" in pro_data.get("message", "").lower()
        print(f"Subscription override to pro: {pro_data.get('message')}")
        
        # Verify user is pro
        detail_resp = admin_session.get(f"{BASE_URL}/api/admin/users/{test_user_id}")
        assert detail_resp.status_code == 200
        user = detail_resp.json()["user"]
        assert user.get("subscription_status") == "active"
        assert user.get("subscription_override") == True
        
        # Set back to free
        free_resp = admin_session.post(
            f"{BASE_URL}/api/admin/users/{test_user_id}/subscription",
            json={"plan": "free"}
        )
        assert free_resp.status_code == 200
        print(f"Subscription override to free: {free_resp.json().get('message')}")


class TestAdminSecurity:
    """Test security monitoring endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        session = requests.Session()
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fuzailbukhari@gmail.com",
            "password": "Admin1234!"
        })
        assert login_resp.status_code == 200
        data = login_resp.json()
        csrf_token = data.get("csrf_token")
        if csrf_token:
            session.headers.update({"X-CSRF-Token": csrf_token})
        return session
    
    def test_security_summary(self, admin_session):
        """GET /api/admin/security/summary returns security metrics"""
        resp = admin_session.get(f"{BASE_URL}/api/admin/security/summary")
        assert resp.status_code == 200, f"Security summary failed: {resp.text}"
        data = resp.json()
        
        required_fields = [
            "failed_logins_24h", "failed_logins_7d",
            "locked_accounts", "banned_users", "top_offending_ips"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        assert isinstance(data["top_offending_ips"], list)
        print(f"Security summary: failed_24h={data['failed_logins_24h']}, locked={data['locked_accounts']}, banned={data['banned_users']}")
    
    def test_failed_logins_list(self, admin_session):
        """GET /api/admin/security/failed-logins returns paginated list"""
        resp = admin_session.get(f"{BASE_URL}/api/admin/security/failed-logins?page=1&limit=10")
        assert resp.status_code == 200, f"Failed logins list failed: {resp.text}"
        data = resp.json()
        
        assert "logs" in data
        assert "total" in data
        assert "page" in data
        print(f"Failed logins: {len(data['logs'])} logs, total={data['total']}")
    
    def test_lockouts_list(self, admin_session):
        """GET /api/admin/security/lockouts returns locked accounts"""
        resp = admin_session.get(f"{BASE_URL}/api/admin/security/lockouts")
        assert resp.status_code == 200, f"Lockouts list failed: {resp.text}"
        data = resp.json()
        
        assert "locked_accounts" in data
        assert isinstance(data["locked_accounts"], list)
        print(f"Locked accounts: {len(data['locked_accounts'])}")


class TestAdminAuditLogs:
    """Test audit log endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        session = requests.Session()
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fuzailbukhari@gmail.com",
            "password": "Admin1234!"
        })
        assert login_resp.status_code == 200
        data = login_resp.json()
        csrf_token = data.get("csrf_token")
        if csrf_token:
            session.headers.update({"X-CSRF-Token": csrf_token})
        return session
    
    def test_audit_logs_paginated(self, admin_session):
        """GET /api/admin/audit-logs returns paginated logs"""
        resp = admin_session.get(f"{BASE_URL}/api/admin/audit-logs?page=1&limit=20")
        assert resp.status_code == 200, f"Audit logs failed: {resp.text}"
        data = resp.json()
        
        assert "logs" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        assert isinstance(data["logs"], list)
        print(f"Audit logs: {len(data['logs'])} logs on page {data['page']}/{data['pages']}, total={data['total']}")
    
    def test_audit_logs_with_type_filter(self, admin_session):
        """GET /api/admin/audit-logs with log_type filter"""
        resp = admin_session.get(f"{BASE_URL}/api/admin/audit-logs?log_type=admin_action")
        assert resp.status_code == 200
        data = resp.json()
        assert "logs" in data
        # All logs should be admin_action type
        for log in data["logs"]:
            assert log.get("type") == "admin_action"
        print(f"Filtered audit logs (admin_action): {len(data['logs'])} logs")
    
    def test_audit_log_types(self, admin_session):
        """GET /api/admin/audit-logs/types returns distinct log types"""
        resp = admin_session.get(f"{BASE_URL}/api/admin/audit-logs/types")
        assert resp.status_code == 200, f"Audit log types failed: {resp.text}"
        data = resp.json()
        
        assert "types" in data
        assert isinstance(data["types"], list)
        print(f"Audit log types: {data['types']}")


class TestAdminSupport:
    """Test support tools endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        session = requests.Session()
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fuzailbukhari@gmail.com",
            "password": "Admin1234!"
        })
        assert login_resp.status_code == 200
        data = login_resp.json()
        csrf_token = data.get("csrf_token")
        if csrf_token:
            session.headers.update({"X-CSRF-Token": csrf_token})
        return session
    
    def test_support_search(self, admin_session):
        """GET /api/admin/support/search?q=test returns matching users"""
        resp = admin_session.get(f"{BASE_URL}/api/admin/support/search?q=test")
        assert resp.status_code == 200, f"Support search failed: {resp.text}"
        data = resp.json()
        
        assert "users" in data
        assert isinstance(data["users"], list)
        # Should find test@demo.com
        emails = [u.get("email") for u in data["users"]]
        assert any("test" in e.lower() for e in emails if e), f"Expected to find test user, got: {emails}"
        print(f"Support search 'test': found {len(data['users'])} users")
    
    def test_support_search_short_query(self, admin_session):
        """GET /api/admin/support/search with short query returns empty"""
        resp = admin_session.get(f"{BASE_URL}/api/admin/support/search?q=a")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("users") == []
        print("Support search with short query correctly returns empty")
    
    def test_send_notification(self, admin_session):
        """POST /api/admin/support/send-notification sends notification to user"""
        # First get test user id
        search_resp = admin_session.get(f"{BASE_URL}/api/admin/support/search?q=test@demo.com")
        assert search_resp.status_code == 200
        users = search_resp.json().get("users", [])
        assert len(users) > 0
        test_user_id = users[0]["user_id"]
        
        # Send notification
        notif_resp = admin_session.post(
            f"{BASE_URL}/api/admin/support/send-notification",
            json={
                "user_id": test_user_id,
                "message": "Test notification from admin pytest",
                "type": "info"
            }
        )
        assert notif_resp.status_code == 200, f"Send notification failed: {notif_resp.text}"
        data = notif_resp.json()
        assert "sent" in data.get("message", "").lower()
        print(f"Notification sent: {data.get('message')}")


class TestAdminExport:
    """Test user export functionality"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        session = requests.Session()
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "fuzailbukhari@gmail.com",
            "password": "Admin1234!"
        })
        assert login_resp.status_code == 200
        data = login_resp.json()
        csrf_token = data.get("csrf_token")
        if csrf_token:
            session.headers.update({"X-CSRF-Token": csrf_token})
        return session
    
    def test_export_users_csv(self, admin_session):
        """GET /api/admin/users/export/csv returns CSV file"""
        resp = admin_session.get(f"{BASE_URL}/api/admin/users/export/csv")
        assert resp.status_code == 200, f"Export CSV failed: {resp.text}"
        
        # Check content type
        content_type = resp.headers.get("content-type", "")
        assert "text/csv" in content_type, f"Expected text/csv, got: {content_type}"
        
        # Check content disposition
        content_disp = resp.headers.get("content-disposition", "")
        assert "attachment" in content_disp
        assert "users_export" in content_disp
        
        # Verify CSV content
        content = resp.text
        assert "user_id" in content or "email" in content
        print(f"CSV export successful, {len(content)} bytes")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
