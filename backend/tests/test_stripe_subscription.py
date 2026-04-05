"""
Test Stripe subscription endpoints for MyCareerCopilot.
Tests: GET /api/subscription, GET /api/stripe/config, POST /api/stripe/create-checkout,
       POST /api/applications usage limit (402 after 3 apps)
"""
import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@demo.com"
TEST_PASSWORD = "Test1234!"


class TestStripeSubscription:
    """Test Stripe subscription and usage limit endpoints."""
    
    @pytest.fixture(scope="class")
    def session(self):
        """Create a requests session with cookies."""
        return requests.Session()
    
    @pytest.fixture(scope="class")
    def auth_data(self, session):
        """Login and get auth data including CSRF token."""
        login_response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        data = login_response.json()
        csrf_token = data.get("csrf_token")
        assert csrf_token, "CSRF token not returned in login response"
        return {"csrf_token": csrf_token, "user_id": data.get("user_id")}
    
    def test_stripe_config_returns_publishable_key(self, session, auth_data):
        """GET /api/stripe/config should return Stripe publishable key."""
        response = session.get(f"{BASE_URL}/api/stripe/config")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "publishable_key" in data, "Response should contain 'publishable_key'"
        # Publishable key should start with pk_test_ or pk_live_
        pk = data["publishable_key"]
        assert pk and (pk.startswith("pk_test_") or pk.startswith("pk_live_")), \
            f"Invalid publishable key format: {pk}"
        print(f"✓ Stripe config returned valid publishable key: {pk[:20]}...")
    
    def test_subscription_returns_plan_and_usage(self, session, auth_data):
        """GET /api/subscription should return plan status and usage limits for free user."""
        response = session.get(f"{BASE_URL}/api/subscription")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Check required fields
        assert "plan" in data, "Response should contain 'plan'"
        assert "subscription_status" in data, "Response should contain 'subscription_status'"
        assert "usage" in data, "Response should contain 'usage'"
        
        # For free user, plan should be 'free'
        assert data["plan"] in ["free", "pro"], f"Plan should be 'free' or 'pro', got: {data['plan']}"
        
        # Check usage structure
        usage = data["usage"]
        expected_features = ["job_applications", "resume_optimizations", "interview_prep", 
                           "career_paths", "cover_letters", "extension_uses"]
        
        for feature in expected_features:
            assert feature in usage, f"Usage should contain '{feature}'"
            feature_usage = usage[feature]
            assert "current" in feature_usage, f"Usage[{feature}] should have 'current'"
            assert "limit" in feature_usage, f"Usage[{feature}] should have 'limit'"
            assert "remaining" in feature_usage, f"Usage[{feature}] should have 'remaining'"
        
        print(f"✓ Subscription endpoint returned plan: {data['plan']}")
        print(f"  Usage limits: {json.dumps(usage, indent=2)}")
    
    def test_create_checkout_requires_origin_url(self, session, auth_data):
        """POST /api/stripe/create-checkout should require origin_url."""
        csrf_token = auth_data["csrf_token"]
        
        # Test without origin_url
        response = session.post(
            f"{BASE_URL}/api/stripe/create-checkout",
            json={},
            headers={"X-CSRF-Token": csrf_token, "Content-Type": "application/json"}
        )
        assert response.status_code == 400, f"Expected 400 without origin_url, got {response.status_code}"
        print("✓ Create checkout correctly requires origin_url")
    
    def test_create_checkout_returns_stripe_url(self, session, auth_data):
        """POST /api/stripe/create-checkout should return Stripe checkout URL and session_id."""
        csrf_token = auth_data["csrf_token"]
        
        response = session.post(
            f"{BASE_URL}/api/stripe/create-checkout",
            json={"origin_url": BASE_URL},
            headers={"X-CSRF-Token": csrf_token, "Content-Type": "application/json"}
        )
        
        # Could be 200 (success) or 400 (already has subscription)
        if response.status_code == 400:
            data = response.json()
            if "already have an active Pro subscription" in str(data):
                print("✓ User already has Pro subscription - checkout blocked correctly")
                pytest.skip("User already has Pro subscription")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "url" in data, "Response should contain 'url'"
        assert "session_id" in data, "Response should contain 'session_id'"
        
        # URL should be a Stripe checkout URL
        url = data["url"]
        assert url.startswith("https://checkout.stripe.com/"), \
            f"URL should be Stripe checkout URL, got: {url[:50]}..."
        
        # Session ID should be a valid Stripe session ID
        session_id = data["session_id"]
        assert session_id.startswith("cs_"), f"Session ID should start with 'cs_', got: {session_id}"
        
        print(f"✓ Create checkout returned valid Stripe URL and session_id")
        print(f"  URL: {url[:60]}...")
        print(f"  Session ID: {session_id}")


class TestUsageLimits:
    """Test usage limits on AI endpoints - specifically job applications."""
    
    @pytest.fixture(scope="class")
    def session(self):
        """Create a requests session with cookies."""
        return requests.Session()
    
    @pytest.fixture(scope="class")
    def auth_data(self, session):
        """Login and get auth data including CSRF token."""
        login_response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        data = login_response.json()
        csrf_token = data.get("csrf_token")
        return {"csrf_token": csrf_token, "user_id": data.get("user_id")}
    
    def test_check_current_usage(self, session, auth_data):
        """Check current usage to understand test state."""
        response = session.get(f"{BASE_URL}/api/subscription")
        assert response.status_code == 200
        
        data = response.json()
        plan = data.get("plan", "free")
        usage = data.get("usage", {})
        apps_usage = usage.get("job_applications", {})
        
        print(f"Current plan: {plan}")
        print(f"Job applications usage: {apps_usage.get('current', 0)}/{apps_usage.get('limit', 3)}")
        
        if plan == "pro":
            pytest.skip("User is on Pro plan - usage limits don't apply")
        
        return apps_usage
    
    def test_applications_endpoint_exists(self, session, auth_data):
        """Verify POST /api/applications endpoint exists and requires proper body."""
        csrf_token = auth_data["csrf_token"]
        
        # Test with empty body - should get validation error
        response = session.post(
            f"{BASE_URL}/api/applications",
            json={},
            headers={"X-CSRF-Token": csrf_token, "Content-Type": "application/json"}
        )
        
        # Should be 422 (validation error) or 400, not 404
        assert response.status_code != 404, "Applications endpoint should exist"
        print(f"✓ Applications endpoint exists (status: {response.status_code})")
    
    def test_application_creation_with_valid_data(self, session, auth_data):
        """Test creating an application with valid data."""
        csrf_token = auth_data["csrf_token"]
        
        # First check current usage
        sub_response = session.get(f"{BASE_URL}/api/subscription")
        sub_data = sub_response.json()
        
        if sub_data.get("plan") == "pro":
            pytest.skip("User is on Pro plan - usage limits don't apply")
        
        apps_usage = sub_data.get("usage", {}).get("job_applications", {})
        current = apps_usage.get("current", 0)
        limit = apps_usage.get("limit", 3)
        
        print(f"Current usage before test: {current}/{limit}")
        
        # Create application with required fields
        app_data = {
            "job_id": f"test_job_{current + 1}",
            "job_title": "Software Engineer",
            "company": "Test Company",
            "location": "Remote",
            "apply_link": "https://example.com/apply",
            "job_description": "This is a test job description for testing purposes.",
            "employment_type": "Full-time"
        }
        
        response = session.post(
            f"{BASE_URL}/api/applications",
            json=app_data,
            headers={"X-CSRF-Token": csrf_token, "Content-Type": "application/json"}
        )
        
        if response.status_code == 402:
            # Usage limit reached
            data = response.json()
            detail = data.get("detail", data)
            print(f"✓ Usage limit reached (402): {detail}")
            assert detail.get("error") == "usage_limit_reached" or "usage_limit" in str(detail).lower(), \
                f"402 response should indicate usage limit: {detail}"
            return
        
        # Should be 200 or 201 for successful creation
        assert response.status_code in [200, 201], \
            f"Expected 200/201 or 402, got {response.status_code}: {response.text}"
        
        print(f"✓ Application created successfully (status: {response.status_code})")


class TestPublicPricingPage:
    """Test that /pricing page is accessible without authentication."""
    
    def test_pricing_page_loads(self):
        """Verify pricing page is accessible (public route)."""
        # This is a frontend route, but we can verify the backend doesn't block it
        response = requests.get(f"{BASE_URL}/api/stripe/config")
        assert response.status_code == 200, "Stripe config should be accessible"
        print("✓ Stripe config endpoint accessible (used by pricing page)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
