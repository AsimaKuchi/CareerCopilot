"""
Unit tests for profile_schema.py migration functions.
Tests migrate_profile_to_v2() and get_autofill_data() key outputs.
"""

import pytest
import sys
sys.path.insert(0, '/app/backend')

from profile_schema import (
    migrate_profile_to_v2,
    get_autofill_data,
    normalize_phone,
    normalize_work_authorization,
    normalize_skills,
    normalize_skill,
    get_skill_names,
    bucket_to_years,
    years_to_bucket,
    WorkAuthorizationStatus,
    SeniorityLevel,
    EducationLevel,
)


class TestPhoneNormalization:
    """Test phone number normalization to E.164 format."""
    
    def test_us_phone_10_digits(self):
        result = normalize_phone("4165551234", "Canada")
        assert result["normalized"] == "+14165551234"
        assert result["formatted"] == "+1 (416) 555-1234"
        assert result["metadata"]["countryCode"] == "+1"
    
    def test_us_phone_with_formatting(self):
        result = normalize_phone("(416) 555-1234", "Canada")
        assert result["normalized"] == "+14165551234"
    
    def test_us_phone_11_digits_with_1(self):
        result = normalize_phone("14165551234")
        assert result["normalized"] == "+14165551234"
    
    def test_phone_with_plus(self):
        result = normalize_phone("+14165551234")
        assert result["normalized"] == "+14165551234"
    
    def test_empty_phone(self):
        result = normalize_phone("")
        assert result["normalized"] is None
    
    def test_none_phone(self):
        result = normalize_phone(None)
        assert result["normalized"] is None


class TestWorkAuthorizationNormalization:
    """Test work authorization normalization."""
    
    def test_citizen(self):
        result = normalize_work_authorization("citizen", "CA")
        assert result["normalized"]["status"] == "citizen"
        assert result["normalized"]["requiresSponsorship"] == False
        assert result["normalized"]["country"] == "CA"
    
    def test_canadian_citizen(self):
        result = normalize_work_authorization("canadian_citizen")
        assert result["normalized"]["status"] == "citizen"
        assert result["normalized"]["country"] == "CA"
    
    def test_permanent_resident(self):
        result = normalize_work_authorization("permanent_resident", "CA")
        assert result["normalized"]["status"] == "permanent_resident"
        assert result["normalized"]["requiresSponsorship"] == False
    
    def test_pgwp(self):
        result = normalize_work_authorization("pgwp")
        assert result["normalized"]["status"] == "pgwp"
        assert result["normalized"]["requiresSponsorship"] == True
        assert result["normalized"]["country"] == "CA"
    
    def test_h1b(self):
        result = normalize_work_authorization("h1b")
        assert result["normalized"]["status"] == "h1b"
        assert result["normalized"]["requiresSponsorship"] == True
        assert result["normalized"]["country"] == "US"
    
    def test_require_sponsorship(self):
        result = normalize_work_authorization("require_sponsorship")
        assert result["normalized"]["status"] == "require_sponsorship"
        assert result["normalized"]["requiresSponsorship"] == True
    
    def test_unknown(self):
        result = normalize_work_authorization("something_random")
        assert result["normalized"]["status"] == "unknown"
    
    def test_empty(self):
        result = normalize_work_authorization("")
        assert result["normalized"]["status"] == "unknown"


class TestSkillsNormalization:
    """Test skills normalization with numeric years."""
    
    def test_string_skills(self):
        result = normalize_skills(["Python", "JavaScript", "SQL"])
        assert len(result["items"]) == 3
        assert result["items"][0]["name"] == "Python"
        assert result["items"][0]["years"] is None
    
    def test_skills_with_bucket_years(self):
        skills = [
            {"name": "Python", "years": "3-5"},
            {"name": "JavaScript", "years": "<1"}
        ]
        result = normalize_skills(skills)
        assert result["items"][0]["name"] == "Python"
        assert result["items"][0]["years"] == 4  # Midpoint of 3-5
        assert result["items"][1]["years"] == 0.5  # Midpoint of <1
    
    def test_skills_with_numeric_years(self):
        skills = [
            {"name": "Python", "years": 5},
            {"name": "JavaScript", "years": 2}
        ]
        result = normalize_skills(skills)
        assert result["items"][0]["years"] == 5
        assert result["items"][1]["years"] == 2
    
    def test_empty_skills(self):
        result = normalize_skills([])
        assert result["items"] == []
    
    def test_none_skills(self):
        result = normalize_skills(None)
        assert result["items"] == []


class TestYearsBucketConversion:
    """Test conversion between numeric years and buckets."""
    
    def test_years_to_bucket_less_than_1(self):
        assert years_to_bucket(0.5) == "<1"
        assert years_to_bucket(0) == "<1"
    
    def test_years_to_bucket_1_to_2(self):
        assert years_to_bucket(1) == "1-2"
        assert years_to_bucket(2) == "1-2"
        assert years_to_bucket(2.5) == "1-2"
    
    def test_years_to_bucket_3_to_5(self):
        assert years_to_bucket(3) == "3-5"
        assert years_to_bucket(5) == "3-5"
        assert years_to_bucket(5.5) == "3-5"
    
    def test_years_to_bucket_5_plus(self):
        assert years_to_bucket(6) == "5+"
        assert years_to_bucket(10) == "5+"
    
    def test_bucket_to_years(self):
        assert bucket_to_years("<1") == 0.5
        assert bucket_to_years("1-2") == 1.5
        assert bucket_to_years("1–2") == 1.5  # Unicode dash
        assert bucket_to_years("3-5") == 4
        assert bucket_to_years("5+") == 7


class TestGetSkillNames:
    """Test extracting skill names from various formats."""
    
    def test_string_list(self):
        skills = ["Python", "JavaScript", "SQL"]
        result = get_skill_names(skills)
        assert result == ["python", "javascript", "sql"]
    
    def test_dict_list(self):
        skills = [
            {"name": "Python", "years": 5},
            {"name": "JavaScript", "years": 2}
        ]
        result = get_skill_names(skills)
        assert result == ["python", "javascript"]
    
    def test_structured_format(self):
        skills = {
            "items": [
                {"name": "Python", "years": 5},
                {"name": "JavaScript", "years": 2}
            ]
        }
        result = get_skill_names(skills)
        assert result == ["python", "javascript"]
    
    def test_empty(self):
        assert get_skill_names([]) == []
        assert get_skill_names(None) == []


class TestMigrateProfileToV2:
    """Test full profile migration from v1 to v2."""
    
    def test_basic_migration(self):
        v1_profile = {
            "user_id": "test123",
            "email": "test@example.com",
            "skills": ["Python", "JavaScript"],
            "work_authorization": "canadian_citizen",
            "seniority_level": "senior",
            "highest_education": "bachelor",
            "phone_number": "4165551234",
            "address_city": "Toronto",
            "address_state": "Ontario",
            "address_country": "Canada",
            "salary_min": 80000,
            "salary_max": 120000,
        }
        
        result = migrate_profile_to_v2(v1_profile)
        
        # Check version
        assert result["profile_version"] == 2
        assert "migrated_at" in result
        
        # Check structured data exists
        assert "structured" in result
        structured = result["structured"]
        
        # Check work authorization
        assert structured["workAuthorization"]["normalized"]["status"] == "citizen"
        assert structured["workAuthorization"]["normalized"]["requiresSponsorship"] == False
        
        # Check skills
        assert len(structured["skills"]["items"]) == 2
        assert structured["skills"]["items"][0]["name"] == "Python"
        
        # Check contact
        assert structured["contact"]["phone"]["normalized"] == "+14165551234"
        assert structured["contact"]["location"]["normalized"]["city"] == "Toronto"
        
        # Check compensation
        assert structured["compensation"]["salaryExpectations"]["min"] == 80000
        assert structured["compensation"]["salaryExpectations"]["max"] == 120000
    
    def test_migration_preserves_original_fields(self):
        v1_profile = {
            "user_id": "test123",
            "custom_field": "custom_value",
            "phone_number": "4165551234",
        }
        
        result = migrate_profile_to_v2(v1_profile)
        
        # Original fields preserved
        assert result["user_id"] == "test123"
        assert result["custom_field"] == "custom_value"
        assert result["phone_number"] == "4165551234"
    
    def test_migration_idempotent(self):
        v1_profile = {
            "user_id": "test123",
            "work_authorization": "citizen",
        }
        
        v2_profile = migrate_profile_to_v2(v1_profile)
        v2_again = migrate_profile_to_v2(v2_profile)
        
        # Should still be v2
        assert v2_again["profile_version"] == 2
        assert "structured" in v2_again


class TestGetAutofillData:
    """Test auto-fill data extraction."""
    
    def test_autofill_phone_e164(self):
        profile = {
            "profile_version": 2,
            "structured": {
                "contact": {
                    "email": "test@example.com",
                    "phone": {
                        "raw": "(416) 555-1234",
                        "normalized": "+14165551234",
                        "formatted": "+1 (416) 555-1234",
                        "metadata": {"countryCode": "+1"}
                    },
                    "location": {
                        "normalized": {"city": "Toronto", "state": "ON", "countryCode": "CA"}
                    }
                },
                "workAuthorization": {
                    "normalized": {"status": "citizen", "country": "CA", "requiresSponsorship": False}
                },
                "skills": {"items": []},
                "links": {},
                "preferences": {},
                "compensation": {"salaryExpectations": {}},
                "industries": {},
                "applicationDefaults": {},
                "seniorityLevel": {"normalized": "senior"},
                "education": {"normalized": "bachelor"},
            }
        }
        
        result = get_autofill_data(profile)
        
        # Check E.164 format for forms
        assert result["phone"] == "+14165551234"
        # Check formatted for display
        assert result["phoneFormatted"] == "+1 (416) 555-1234"
    
    def test_autofill_work_authorization(self):
        profile = {
            "work_authorization": "pgwp",
            "address_country": "Canada",
        }
        
        result = get_autofill_data(profile)
        
        assert result["workAuthorizationStatus"] == "pgwp"
        assert result["requiresSponsorship"] == True
    
    def test_autofill_skills_with_years(self):
        profile = {
            "skills": [
                {"name": "Python", "years": 5},
                {"name": "JavaScript", "years": 2}
            ]
        }
        
        result = get_autofill_data(profile)
        
        # Simple list
        assert result["skills"] == ["Python", "JavaScript"]
        
        # With years
        assert result["skillsWithYears"][0]["name"] == "Python"
        assert result["skillsWithYears"][0]["years"] == 5
        assert result["skillsWithYears"][0]["yearsBucket"] == "3-5"
        
        assert result["skillsWithYears"][1]["name"] == "JavaScript"
        assert result["skillsWithYears"][1]["years"] == 2
        assert result["skillsWithYears"][1]["yearsBucket"] == "1-2"
    
    def test_autofill_from_v1_profile(self):
        """Test that v1 profiles are auto-migrated."""
        v1_profile = {
            "user_id": "test123",
            "email": "test@example.com",
            "phone_number": "4165551234",
            "skills": ["Python", "SQL"],
            "work_authorization": "citizen",
            "address_city": "Toronto",
            "address_state": "Ontario",
            "address_country": "Canada",
        }
        
        result = get_autofill_data(v1_profile)
        
        assert result["email"] == "test@example.com"
        assert result["phone"] == "+14165551234"
        assert result["city"] == "Toronto"
        assert result["workAuthorizationStatus"] == "citizen"
        assert "Python" in result["skills"]


class TestCanadaWorkAuthorizations:
    """Test all Canada-specific work authorization statuses."""
    
    def test_all_canada_statuses(self):
        canada_statuses = [
            ("citizen", "citizen", False),
            ("canadian_citizen", "citizen", False),
            ("permanent_resident", "permanent_resident", False),
            ("open_work_permit", "open_work_permit", True),
            ("pgwp", "pgwp", True),
            ("employer_specific_work_permit", "employer_specific_work_permit", True),
            ("student", "student", True),
            ("not_authorized", "not_authorized", True),
        ]
        
        for raw, expected_status, expected_sponsorship in canada_statuses:
            result = normalize_work_authorization(raw, "CA")
            assert result["normalized"]["status"] == expected_status, f"Failed for {raw}"
            assert result["normalized"]["requiresSponsorship"] == expected_sponsorship, f"Sponsorship failed for {raw}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
