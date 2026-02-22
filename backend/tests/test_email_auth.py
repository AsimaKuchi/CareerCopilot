"""
Email Authentication API Tests
Tests for: signup, login, verify-email, forgot-password, reset-password
"""

import pytest
import requests
import os
import uuid

# Get API URL from environment - DO NOT add default URL
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data
TEST_EMAIL_PREFIX = "TEST_emailauth_"
TEST_PASSWORD_STRONG = "TestPass123!"
TEST_PASSWORD_WEAK = "weak"
TEST_NAME = "Test User"


class TestHealthAndSetup:
    """Verify API is accessible"""
    
    def test_api_health(self):
        """Check API is running"""
        response = requests.get(f"{BASE_URL}/api/public/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"API Health: {data.get('status')}, Jobs: {data.get('jobs_in_database')}")


class TestSignupEndpoint:
    """Test /api/auth/signup endpoint"""
    
    def test_signup_with_weak_password(self):
        """Weak password should be rejected with error message"""
        unique_email = f"{TEST_EMAIL_PREFIX}{uuid.uuid4().hex[:8]}@example.com"
        response = requests.post(
            f"{BASE_URL}/api/auth/signup",
            json={
                "email": unique_email,
                "password": "weak",  # Too short
                "name": TEST_NAME
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        # Check error mentions password requirement
        assert "8" in data["detail"] or "character" in data["detail"].lower()
        print(f"Weak password rejected: {data['detail']}")
    
    def test_signup_password_missing_uppercase(self):
        """Password without uppercase should be rejected"""
        unique_email = f"{TEST_EMAIL_PREFIX}{uuid.uuid4().hex[:8]}@example.com"
        response = requests.post(
            f"{BASE_URL}/api/auth/signup",
            json={
                "email": unique_email,
                "password": "testpass123!",  # No uppercase
                "name": TEST_NAME
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "uppercase" in data["detail"].lower()
        print(f"Missing uppercase rejected: {data['detail']}")
    
    def test_signup_password_missing_number(self):
        """Password without number should be rejected"""
        unique_email = f"{TEST_EMAIL_PREFIX}{uuid.uuid4().hex[:8]}@example.com"
        response = requests.post(
            f"{BASE_URL}/api/auth/signup",
            json={
                "email": unique_email,
                "password": "TestPass!@#",  # No number
                "name": TEST_NAME
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "number" in data["detail"].lower()
        print(f"Missing number rejected: {data['detail']}")
    
    def test_signup_password_missing_special_char(self):
        """Password without special character should be rejected"""
        unique_email = f"{TEST_EMAIL_PREFIX}{uuid.uuid4().hex[:8]}@example.com"
        response = requests.post(
            f"{BASE_URL}/api/auth/signup",
            json={
                "email": unique_email,
                "password": "TestPass123",  # No special char
                "name": TEST_NAME
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "special" in data["detail"].lower()
        print(f"Missing special char rejected: {data['detail']}")
    
    def test_signup_with_strong_password(self):
        """Signup with strong password should succeed"""
        unique_email = f"{TEST_EMAIL_PREFIX}{uuid.uuid4().hex[:8]}@example.com"
        response = requests.post(
            f"{BASE_URL}/api/auth/signup",
            json={
                "email": unique_email,
                "password": TEST_PASSWORD_STRONG,
                "name": TEST_NAME
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        # Check for verification-related message
        assert "verify" in data["message"].lower() or "email" in data["message"].lower()
        print(f"Signup success: {data['message']}")
        # May have verification_url in test mode
        if "verification_url" in data:
            print(f"Verification URL provided (test mode): {data['verification_url'][:50]}...")
    
    def test_signup_invalid_email_format(self):
        """Invalid email format should be rejected"""
        response = requests.post(
            f"{BASE_URL}/api/auth/signup",
            json={
                "email": "not-an-email",
                "password": TEST_PASSWORD_STRONG,
                "name": TEST_NAME
            }
        )
        # Should return 422 (validation error) or 400
        assert response.status_code in [400, 422]
        print(f"Invalid email rejected with status: {response.status_code}")


class TestLoginEndpoint:
    """Test /api/auth/login endpoint"""
    
    def test_login_with_nonexistent_email(self):
        """Login with non-existent email should fail"""
        unique_email = f"nonexistent_{uuid.uuid4().hex[:8]}@example.com"
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": unique_email,
                "password": TEST_PASSWORD_STRONG
            }
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        print(f"Nonexistent email login rejected: {data['detail']}")
    
    def test_login_with_wrong_password(self):
        """Login with wrong password should fail"""
        # First create a user
        unique_email = f"{TEST_EMAIL_PREFIX}{uuid.uuid4().hex[:8]}@example.com"
        requests.post(
            f"{BASE_URL}/api/auth/signup",
            json={
                "email": unique_email,
                "password": TEST_PASSWORD_STRONG,
                "name": TEST_NAME
            }
        )
        
        # Try to login with wrong password
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": unique_email,
                "password": "WrongPass123!"
            }
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        print(f"Wrong password login rejected: {data['detail']}")
    
    def test_login_with_unverified_email(self):
        """Login with unverified email should return appropriate error"""
        unique_email = f"{TEST_EMAIL_PREFIX}{uuid.uuid4().hex[:8]}@example.com"
        # Create user (email will be unverified)
        requests.post(
            f"{BASE_URL}/api/auth/signup",
            json={
                "email": unique_email,
                "password": TEST_PASSWORD_STRONG,
                "name": TEST_NAME
            }
        )
        
        # Try to login
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": unique_email,
                "password": TEST_PASSWORD_STRONG
            }
        )
        assert response.status_code == 401
        data = response.json()
        # Should mention email verification
        assert "verify" in data["detail"].lower()
        print(f"Unverified email login rejected: {data['detail']}")


class TestVerifyEmailEndpoint:
    """Test /api/auth/verify-email endpoint"""
    
    def test_verify_email_without_token(self):
        """Verify email without token should fail"""
        response = requests.post(
            f"{BASE_URL}/api/auth/verify-email",
            json={}
        )
        assert response.status_code == 400
        print(f"Missing token rejected with status: {response.status_code}")
    
    def test_verify_email_with_invalid_token(self):
        """Verify email with invalid token should fail"""
        response = requests.post(
            f"{BASE_URL}/api/auth/verify-email",
            json={"token": "invalid_token_12345"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "invalid" in data["detail"].lower() or "expired" in data["detail"].lower()
        print(f"Invalid token rejected: {data['detail']}")
    
    def test_verify_email_with_valid_token(self):
        """Verify email with valid token should succeed"""
        # Create user and get verification URL
        unique_email = f"{TEST_EMAIL_PREFIX}{uuid.uuid4().hex[:8]}@example.com"
        signup_response = requests.post(
            f"{BASE_URL}/api/auth/signup",
            json={
                "email": unique_email,
                "password": TEST_PASSWORD_STRONG,
                "name": TEST_NAME
            }
        )
        signup_data = signup_response.json()
        
        # Extract token from verification URL if available
        if "verification_url" in signup_data:
            verification_url = signup_data["verification_url"]
            # Extract token from URL
            token = verification_url.split("token=")[1] if "token=" in verification_url else None
            
            if token:
                response = requests.post(
                    f"{BASE_URL}/api/auth/verify-email",
                    json={"token": token}
                )
                assert response.status_code == 200
                data = response.json()
                assert "verified" in data["message"].lower() or "success" in data["message"].lower()
                print(f"Email verification success: {data['message']}")
            else:
                print("Could not extract token from verification URL")
                pytest.skip("Verification URL format unexpected")
        else:
            print("Verification URL not provided (email might have been sent)")
            pytest.skip("Verification URL not available in test mode")


class TestForgotPasswordEndpoint:
    """Test /api/auth/forgot-password endpoint"""
    
    def test_forgot_password_with_valid_email(self):
        """Forgot password with valid email should return success"""
        # Create user first
        unique_email = f"{TEST_EMAIL_PREFIX}{uuid.uuid4().hex[:8]}@example.com"
        requests.post(
            f"{BASE_URL}/api/auth/signup",
            json={
                "email": unique_email,
                "password": TEST_PASSWORD_STRONG,
                "name": TEST_NAME
            }
        )
        
        response = requests.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": unique_email}
        )
        assert response.status_code == 200
        data = response.json()
        # Should return generic message (security - don't reveal if email exists)
        assert "message" in data
        print(f"Forgot password response: {data['message']}")
    
    def test_forgot_password_with_nonexistent_email(self):
        """Forgot password with non-existent email should still return success (security)"""
        response = requests.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": f"nonexistent_{uuid.uuid4().hex[:8]}@example.com"}
        )
        # Should still return 200 for security (don't reveal if email exists)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"Non-existent email response: {data['message']}")


class TestResetPasswordEndpoint:
    """Test /api/auth/reset-password endpoint"""
    
    def test_reset_password_with_invalid_token(self):
        """Reset password with invalid token should fail"""
        response = requests.post(
            f"{BASE_URL}/api/auth/reset-password",
            json={
                "token": "invalid_reset_token_12345",
                "password": TEST_PASSWORD_STRONG
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "invalid" in data["detail"].lower() or "expired" in data["detail"].lower()
        print(f"Invalid reset token rejected: {data['detail']}")
    
    def test_reset_password_with_weak_password(self):
        """Reset password with weak password should fail validation"""
        response = requests.post(
            f"{BASE_URL}/api/auth/reset-password",
            json={
                "token": "some_token",
                "password": "weak"
            }
        )
        # Should fail with password validation error
        assert response.status_code == 400
        data = response.json()
        assert "8" in data["detail"] or "character" in data["detail"].lower() or "password" in data["detail"].lower()
        print(f"Weak reset password rejected: {data['detail']}")


class TestResendVerificationEndpoint:
    """Test /api/auth/resend-verification endpoint"""
    
    def test_resend_verification_with_valid_email(self):
        """Resend verification for unverified account should succeed"""
        # Create user first
        unique_email = f"{TEST_EMAIL_PREFIX}{uuid.uuid4().hex[:8]}@example.com"
        requests.post(
            f"{BASE_URL}/api/auth/signup",
            json={
                "email": unique_email,
                "password": TEST_PASSWORD_STRONG,
                "name": TEST_NAME
            }
        )
        
        response = requests.post(
            f"{BASE_URL}/api/auth/resend-verification",
            json={"email": unique_email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"Resend verification response: {data['message']}")
    
    def test_resend_verification_with_nonexistent_email(self):
        """Resend verification for non-existent email should return generic success (security)"""
        response = requests.post(
            f"{BASE_URL}/api/auth/resend-verification",
            json={"email": f"nonexistent_{uuid.uuid4().hex[:8]}@example.com"}
        )
        # Should return 200 for security
        assert response.status_code == 200
        print(f"Non-existent email resend response status: {response.status_code}")


class TestCompleteAuthFlow:
    """Test complete authentication flow: signup -> verify -> login"""
    
    def test_full_auth_flow(self):
        """Test complete signup, verify, and login flow"""
        unique_email = f"{TEST_EMAIL_PREFIX}{uuid.uuid4().hex[:8]}@example.com"
        
        # Step 1: Signup
        signup_response = requests.post(
            f"{BASE_URL}/api/auth/signup",
            json={
                "email": unique_email,
                "password": TEST_PASSWORD_STRONG,
                "name": TEST_NAME
            }
        )
        assert signup_response.status_code == 200
        signup_data = signup_response.json()
        print(f"Step 1 - Signup success: {signup_data['message']}")
        
        # Step 2: Try login (should fail - not verified)
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": unique_email,
                "password": TEST_PASSWORD_STRONG
            }
        )
        assert login_response.status_code == 401
        login_data = login_response.json()
        assert "verify" in login_data["detail"].lower()
        print(f"Step 2 - Unverified login blocked: {login_data['detail']}")
        
        # Step 3: Verify email (if verification URL available)
        if "verification_url" in signup_data:
            token = signup_data["verification_url"].split("token=")[1] if "token=" in signup_data["verification_url"] else None
            
            if token:
                verify_response = requests.post(
                    f"{BASE_URL}/api/auth/verify-email",
                    json={"token": token}
                )
                assert verify_response.status_code == 200
                print(f"Step 3 - Email verified")
                
                # Step 4: Login after verification (should succeed)
                login_response = requests.post(
                    f"{BASE_URL}/api/auth/login",
                    json={
                        "email": unique_email,
                        "password": TEST_PASSWORD_STRONG
                    }
                )
                assert login_response.status_code == 200
                login_data = login_response.json()
                assert "user_id" in login_data
                assert login_data["email"] == unique_email.lower()
                print(f"Step 4 - Login success! User ID: {login_data['user_id']}")
            else:
                print("Step 3-4 skipped: Could not extract token")
        else:
            print("Step 3-4 skipped: Verification URL not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
