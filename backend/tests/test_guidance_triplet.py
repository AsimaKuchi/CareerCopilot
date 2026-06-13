"""Tests for the Career-Path Guidance Triplet feature + verifications of
Stripe bypass and CSRF middleware hardening (iteration 31).
"""

import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    raise RuntimeError("REACT_APP_BACKEND_URL not set")

USER_EMAIL = "refactor_test@example.com"
USER_PASS = "TestPass123!"


# ---------------- fixtures ----------------
@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": USER_EMAIL, "password": USER_PASS},
        timeout=20,
    )
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    body = r.json()
    csrf = body.get("csrf_token") or s.cookies.get("csrf_token")
    assert csrf, f"no csrf_token in login response or cookies: {body}"
    s.headers.update({"X-CSRF-Token": csrf, "Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def path_title():
    # Unique per-run path so we don't collide with prior runs.
    return f"TEST_Path_{uuid.uuid4().hex[:8]}"


# ---------------- GET /paths/guidance ----------------
class TestGuidanceGet:
    def test_unknown_path_returns_empty_shape(self, session, path_title):
        r = session.get(
            f"{BASE_URL}/api/paths/guidance",
            params={"path_title": path_title},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data == {"skills_checked": [], "plan_30d": None, "qna": []}

    def test_unauthenticated_blocked(self, path_title):
        # Brand-new session, no cookies
        r = requests.get(
            f"{BASE_URL}/api/paths/guidance",
            params={"path_title": path_title},
            timeout=10,
        )
        assert r.status_code in (401, 403), r.status_code


# ---------------- PUT /paths/guidance/skills ----------------
class TestSkillToggle:
    def test_add_skill(self, session, path_title):
        r = session.put(
            f"{BASE_URL}/api/paths/guidance/skills",
            json={"path_title": path_title, "skill": "SQL", "checked": True},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        assert "SQL" in r.json()["skills_checked"]

    def test_add_same_skill_idempotent(self, session, path_title):
        r = session.put(
            f"{BASE_URL}/api/paths/guidance/skills",
            json={"path_title": path_title, "skill": "SQL", "checked": True},
            timeout=15,
        )
        assert r.status_code == 200
        # Only one occurrence even after re-add
        assert r.json()["skills_checked"].count("SQL") == 1

    def test_persists_in_get(self, session, path_title):
        r = session.get(
            f"{BASE_URL}/api/paths/guidance",
            params={"path_title": path_title},
            timeout=10,
        )
        assert r.status_code == 200
        assert "SQL" in r.json()["skills_checked"]

    def test_uncheck_removes_skill(self, session, path_title):
        r = session.put(
            f"{BASE_URL}/api/paths/guidance/skills",
            json={"path_title": path_title, "skill": "SQL", "checked": False},
            timeout=15,
        )
        assert r.status_code == 200
        assert "SQL" not in r.json()["skills_checked"]

    def test_csrf_header_required(self, path_title):
        """PUT /paths/guidance/skills without X-CSRF-Token must be 403."""
        s = requests.Session()
        r = s.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": USER_EMAIL, "password": USER_PASS},
            timeout=15,
        )
        assert r.status_code == 200
        # Intentionally do NOT set X-CSRF-Token
        r = s.put(
            f"{BASE_URL}/api/paths/guidance/skills",
            json={"path_title": path_title, "skill": "Foo", "checked": True},
            timeout=15,
        )
        assert r.status_code == 403, f"expected 403 without CSRF, got {r.status_code}"


# ---------------- POST /paths/guidance/plan ----------------
@pytest.fixture(scope="module")
def plan_path_data():
    return {
        "skills_you_have": ["Python", "SQL"],
        "skills_to_learn": ["dbt", "Airflow", "Snowflake"],
        "difficulty": "moderate",
        "time_to_transition": "6-9 months",
    }


class TestPlan30d:
    def test_generate_plan_shape(self, session, path_title, plan_path_data):
        r = session.post(
            f"{BASE_URL}/api/paths/guidance/plan",
            json={"path_title": path_title, "path_data": plan_path_data},
            timeout=60,  # LLM call
        )
        assert r.status_code == 200, r.text
        plan = r.json()
        assert "headline" in plan and isinstance(plan["headline"], str)
        assert "weeks" in plan and isinstance(plan["weeks"], list)
        assert len(plan["weeks"]) == 4
        for w in plan["weeks"]:
            assert "week" in w and "focus" in w and "tasks" in w
            assert isinstance(w["tasks"], list) and len(w["tasks"]) >= 1
        assert "success_signal" in plan

    def test_cached_on_second_call(self, session, path_title, plan_path_data):
        r1 = session.post(
            f"{BASE_URL}/api/paths/guidance/plan",
            json={"path_title": path_title, "path_data": plan_path_data},
            timeout=60,
        )
        r2 = session.post(
            f"{BASE_URL}/api/paths/guidance/plan",
            json={"path_title": path_title, "path_data": plan_path_data},
            timeout=15,  # cached, should be fast
        )
        assert r1.status_code == 200 and r2.status_code == 200
        assert r1.json().get("generated_at") == r2.json().get("generated_at"), \
            "Plan should be cached (same generated_at)"

    def test_force_regenerates(self, session, path_title, plan_path_data):
        r1 = session.post(
            f"{BASE_URL}/api/paths/guidance/plan",
            json={"path_title": path_title, "path_data": plan_path_data},
            timeout=60,
        )
        r2 = session.post(
            f"{BASE_URL}/api/paths/guidance/plan?force=true",
            json={"path_title": path_title, "path_data": plan_path_data},
            timeout=60,
        )
        assert r1.status_code == 200 and r2.status_code == 200
        assert r1.json().get("generated_at") != r2.json().get("generated_at"), \
            "force=true should regenerate (different generated_at)"


# ---------------- POST /paths/guidance/ask ----------------
class TestAskCoach:
    def test_ask_returns_answer(self, session, path_title, plan_path_data):
        r = session.post(
            f"{BASE_URL}/api/paths/guidance/ask",
            json={
                "path_title": path_title,
                "question": "What's the single most important skill to start with?",
                "path_data": plan_path_data,
            },
            timeout=60,  # LLM call
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert "question" in body and "answer" in body and "created_at" in body
        assert isinstance(body["answer"], str) and len(body["answer"]) > 0

    def test_qna_appended_to_guidance(self, session, path_title):
        r = session.get(
            f"{BASE_URL}/api/paths/guidance",
            params={"path_title": path_title},
            timeout=10,
        )
        assert r.status_code == 200
        qna = r.json()["qna"]
        assert isinstance(qna, list) and len(qna) >= 1

    def test_empty_question_rejected(self, session, path_title):
        r = session.post(
            f"{BASE_URL}/api/paths/guidance/ask",
            json={"path_title": path_title, "question": "  "},
            timeout=15,
        )
        assert r.status_code == 400


# ---------------- Stripe bypass + /stripe/usage ----------------
class TestStripeBypassAndUsage:
    def test_subscription_returns_pro_for_free_user(self, session):
        r = session.get(f"{BASE_URL}/api/subscription", timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("plan") == "pro", f"expected pro, got {body.get('plan')}"
        # limit -1 means unlimited on at least one feature bucket
        # /api/subscription returns the limits dict under key "usage"
        usage = body.get("usage", {})
        assert usage, f"expected usage dict, got: {body}"
        assert all(v.get("limit") == -1 for v in usage.values()), \
            f"expected all limits=-1 (pro bypass), got: {usage}"

    def test_stripe_usage_endpoint_exists(self, session):
        r = session.get(f"{BASE_URL}/api/stripe/usage", timeout=15)
        assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text}"
        body = r.json()
        assert "plan" in body and "usage" in body
        assert body["plan"] == "pro"


# ---------------- CSRF middleware ----------------
class TestCSRFMiddleware:
    def test_put_profile_without_csrf_returns_403(self):
        s = requests.Session()
        r = s.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": USER_EMAIL, "password": USER_PASS},
            timeout=15,
        )
        assert r.status_code == 200
        # Intentionally do NOT set X-CSRF-Token
        r = s.put(
            f"{BASE_URL}/api/profile",
            json={"full_name": "should not save"},
            timeout=15,
        )
        assert r.status_code == 403, f"expected 403, got {r.status_code}"

    def test_put_profile_with_csrf_returns_2xx(self, session):
        r = session.put(
            f"{BASE_URL}/api/profile",
            json={"full_name": "Refactor Test User"},
            timeout=15,
        )
        assert r.status_code in (200, 204), f"expected 2xx, got {r.status_code}: {r.text}"
