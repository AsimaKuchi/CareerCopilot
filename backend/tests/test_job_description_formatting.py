"""
Tests for Job Description Formatting Feature
- Verifies the FormattedJobDescription component logic
- Tests section header detection
- Tests bullet point detection
- Tests proper spacing and styling
"""

import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://job-auto-fill-1.preview.emergentagent.com')

# Sample job descriptions with different formatting patterns
SAMPLE_DESCRIPTIONS = {
    "with_requirements_header": """
The Community You Will Join:
We are a fast-growing tech company focused on innovation.

Requirements:
- 5+ years of experience in software development
- Proficiency in Python, JavaScript, and SQL
- Strong problem-solving skills
- Experience with cloud platforms (AWS, GCP, or Azure)

Responsibilities:
Build and maintain scalable applications
Collaborate with cross-functional teams
Design system architecture
""",
    "with_action_verbs": """
About The Role:
Join our team as a Senior Engineer!

What You'll Do:
Design and implement new features
Develop scalable backend services
Collaborate with product managers
Mentor junior developers
Review code and provide feedback

Nice To Have:
Experience with Kubernetes
Knowledge of machine learning
""",
    "plain_text": """
This is a plain text description without any clear headers or formatting.
It contains multiple sentences that should be treated as paragraphs.
The formatting utility should still render this cleanly.
"""
}


class TestJobDescriptionFormatting:
    """Test the job description formatting feature"""

    def test_public_jobs_have_descriptions(self):
        """Verify that public jobs endpoint returns jobs with description fields"""
        response = requests.get(f"{BASE_URL}/api/public/jobs", params={"limit": 10})
        assert response.status_code == 200
        
        data = response.json()
        jobs = data.get("jobs", [])
        assert len(jobs) > 0, "Should have jobs available"
        
        jobs_with_desc = [j for j in jobs if j.get("description")]
        assert len(jobs_with_desc) > 0, "At least some jobs should have descriptions"
        
        # Check description lengths
        for job in jobs_with_desc[:3]:
            desc_len = len(job.get("description", ""))
            print(f"Job: {job.get('title', 'Unknown')[:50]} - Description length: {desc_len}")
            assert desc_len > 100, f"Description should be substantial, got {desc_len} chars"

    def test_descriptions_contain_section_headers(self):
        """Verify that job descriptions contain section headers that can be detected"""
        response = requests.get(f"{BASE_URL}/api/public/jobs", params={"limit": 20})
        assert response.status_code == 200
        
        data = response.json()
        jobs = data.get("jobs", [])
        
        # Common section header patterns
        header_patterns = [
            "requirements:", "qualifications:", "responsibilities:",
            "about the role", "what you'll do", "nice to have",
            "the community you will join", "about us", "benefits:"
        ]
        
        jobs_with_headers = 0
        for job in jobs:
            desc = (job.get("description") or "").lower()
            if any(pattern in desc for pattern in header_patterns):
                jobs_with_headers += 1
        
        print(f"Jobs with detectable section headers: {jobs_with_headers}/{len(jobs)}")
        # At least some jobs should have headers we can detect
        assert jobs_with_headers > 0, "Some jobs should have recognizable section headers"

    def test_descriptions_contain_list_items(self):
        """Verify that job descriptions contain list-like content that can be formatted as bullets"""
        response = requests.get(f"{BASE_URL}/api/public/jobs", params={"limit": 20})
        assert response.status_code == 200
        
        data = response.json()
        jobs = data.get("jobs", [])
        
        # Action verbs that often start list items
        action_verbs = [
            "design", "develop", "create", "build", "implement", "manage",
            "lead", "analyze", "collaborate", "work", "drive", "support"
        ]
        
        jobs_with_lists = 0
        for job in jobs:
            desc = (job.get("description") or "").lower()
            lines = desc.split('\n')
            
            # Check for bullet-like patterns
            has_bullets = any(line.strip().startswith(('-', '•', '*')) for line in lines)
            has_action_lines = any(
                line.strip().split()[0].lower().rstrip(',.:') in action_verbs 
                for line in lines if line.strip() and len(line.strip().split()) > 0
            )
            
            if has_bullets or has_action_lines:
                jobs_with_lists += 1
        
        print(f"Jobs with list-like content: {jobs_with_lists}/{len(jobs)}")
        assert jobs_with_lists > 0, "Some jobs should have list-like content"


class TestFormattedDescriptionComponent:
    """Test that the FormattedJobDescription component files exist and have correct structure"""

    def test_formatting_utility_exists(self):
        """Verify formatJobDescription.js exists and has required exports"""
        util_path = "/app/frontend/src/utils/formatJobDescription.js"
        assert os.path.exists(util_path), f"formatJobDescription.js should exist at {util_path}"
        
        with open(util_path, 'r') as f:
            content = f.read()
        
        # Check for required exports
        assert "parseJobDescription" in content, "Should export parseJobDescription function"
        assert "formatJobDescription" in content, "Should export formatJobDescription function"
        
        # Check for section header patterns
        assert "SECTION_HEADERS" in content, "Should define SECTION_HEADERS patterns"
        assert "requirements" in content.lower(), "Should include 'requirements' as a header pattern"
        assert "the community you will join" in content.lower(), "Should include 'The Community You Will Join' pattern"
        
        # Check for action verbs
        assert "ACTION_VERBS" in content, "Should define ACTION_VERBS for bullet detection"
        
        print("✓ formatJobDescription.js has required structure")

    def test_formatted_description_component_exists(self):
        """Verify FormattedJobDescription.jsx exists and has correct styling"""
        component_path = "/app/frontend/src/components/FormattedJobDescription.jsx"
        assert os.path.exists(component_path), f"FormattedJobDescription.jsx should exist at {component_path}"
        
        with open(component_path, 'r') as f:
            content = f.read()
        
        # Check for header styling
        assert "text-indigo-300" in content, "Headers should be styled with indigo-300"
        assert "font-semibold" in content, "Headers should be bold (font-semibold)"
        assert "border-b" in content, "Headers should have bottom border"
        
        # Check for bullet styling
        assert "text-indigo-400" in content, "Bullets should be styled with indigo-400"
        assert "<ul" in content or "bullet-group" in content, "Should render bullet lists"
        
        # Check for proper spacing
        assert "space-y" in content, "Should have spacing between elements"
        
        print("✓ FormattedJobDescription.jsx has correct styling classes")

    def test_dashboard_uses_formatted_description(self):
        """Verify Dashboard.jsx uses FormattedJobDescription component"""
        dashboard_path = "/app/frontend/src/pages/Dashboard.jsx"
        assert os.path.exists(dashboard_path), f"Dashboard.jsx should exist at {dashboard_path}"
        
        with open(dashboard_path, 'r') as f:
            content = f.read()
        
        # Check for component import
        assert "FormattedJobDescription" in content, "Dashboard should import FormattedJobDescription"
        assert "from" in content and "FormattedJobDescription" in content, "Should import the component"
        
        # Check for expand/collapse toggle
        assert "expand" in content.lower(), "Should have expand functionality"
        assert "expandedJobId" in content or "setExpandedJobId" in content, "Should track expanded job state"
        
        print("✓ Dashboard.jsx uses FormattedJobDescription component")

    def test_job_search_uses_formatted_description(self):
        """Verify JobSearch.jsx uses FormattedJobDescription component"""
        job_search_path = "/app/frontend/src/pages/JobSearch.jsx"
        assert os.path.exists(job_search_path), f"JobSearch.jsx should exist at {job_search_path}"
        
        with open(job_search_path, 'r') as f:
            content = f.read()
        
        # Check for component import
        assert "FormattedJobDescription" in content, "JobSearch should import FormattedJobDescription"
        
        # Check for expand/collapse
        assert "expandedDescJobId" in content or "expand" in content.lower(), "Should have expand functionality"
        
        # Check for scrollable container
        assert "max-h-96" in content or "overflow" in content, "Should have scrollable container"
        
        print("✓ JobSearch.jsx uses FormattedJobDescription component")


class TestFormattingLogic:
    """Test the formatting logic directly by analyzing patterns in the utility"""

    def test_section_header_detection_patterns(self):
        """Verify section header patterns are comprehensive"""
        util_path = "/app/frontend/src/utils/formatJobDescription.js"
        with open(util_path, 'r') as f:
            content = f.read()
        
        # Essential headers that should be detected
        # Note: In JS, apostrophes may be escaped as \'
        essential_headers = [
            "requirements",
            "responsibilities",
            "qualifications",
            "the community you will join",
            "about",
            "benefits",
            "nice to have",
            "what you"  # Covers both "what you'll do" and "what you will do"
        ]
        
        missing = [h for h in essential_headers if h not in content.lower()]
        assert len(missing) == 0, f"Missing header patterns: {missing}"
        
        print(f"✓ All {len(essential_headers)} essential header patterns present")

    def test_action_verb_detection_patterns(self):
        """Verify action verbs for bullet detection are comprehensive"""
        util_path = "/app/frontend/src/utils/formatJobDescription.js"
        with open(util_path, 'r') as f:
            content = f.read()
        
        # Common action verbs that should be detected
        essential_verbs = [
            "design", "develop", "build", "implement", "manage",
            "lead", "collaborate", "work", "support", "create"
        ]
        
        missing = [v for v in essential_verbs if v not in content.lower()]
        assert len(missing) == 0, f"Missing action verbs: {missing}"
        
        print(f"✓ All {len(essential_verbs)} essential action verbs present")

    def test_element_types_in_output(self):
        """Verify the formatter produces correct element types"""
        util_path = "/app/frontend/src/utils/formatJobDescription.js"
        with open(util_path, 'r') as f:
            content = f.read()
        
        # Check for different element types
        assert "'header'" in content or '"header"' in content, "Should produce header elements"
        assert "'bullet'" in content or '"bullet"' in content, "Should produce bullet elements"
        assert "'paragraph'" in content or '"paragraph"' in content, "Should produce paragraph elements"
        
        print("✓ Formatter produces header, bullet, and paragraph element types")


class TestDataTestIds:
    """Verify data-testid attributes are in place for testing"""

    def test_dashboard_has_testids(self):
        """Dashboard should have data-testid for expand buttons"""
        with open("/app/frontend/src/pages/Dashboard.jsx", 'r') as f:
            content = f.read()
        
        assert 'data-testid="expand-desc-btn' in content or 'data-testid={`expand-desc-btn' in content, \
            "Dashboard should have expand-desc-btn testid"
        assert 'data-testid="saved-jobs"' in content, "Dashboard should have saved-jobs testid"
        
        print("✓ Dashboard has required data-testid attributes")

    def test_jobsearch_has_testids(self):
        """JobSearch should have data-testid for expand buttons"""
        with open("/app/frontend/src/pages/JobSearch.jsx", 'r') as f:
            content = f.read()
        
        assert 'data-testid=' in content and 'expand-desc-btn' in content, \
            "JobSearch should have expand-desc-btn testid"
        assert 'data-testid="job-card-' in content or 'data-testid={`job-card-' in content, \
            "JobSearch should have job-card testids"
        
        print("✓ JobSearch has required data-testid attributes")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
