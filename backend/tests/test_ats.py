from app.resume_normalize import canonical_resume
from app.scoring.ats import score_job
from app.scoring.jd_clean import clean_jd
from app.scoring.titles import title_in_family
from tests.fixtures_jds import (
    JAVA_RESUME,
    JD_DATA_SCIENTIST,
    JD_FRONTEND_COBOL,
    JD_GOOD_PARTIAL,
    JD_INTERN,
    JD_KEYWORD_TRAP,
    JD_NEEDS_MANUAL,
    JD_NICE_HEAVY,
    JD_NO_HEADING,
    JD_STAFF,
    JD_STRONG_JAVA,
    JD_WEAK_ANDROID,
)


def test_clean_jd_strips_benefits():
    cleaned = clean_jd("Build APIs\nBenefits:\n401k matching\n")
    assert "401k" not in cleaned
    assert "Build APIs" in cleaned


def test_strong_java_backend_is_strong():
    result = score_job(JAVA_RESUME, JD_STRONG_JAVA, "Java Developer")
    assert result["scoring_status"] == "scored"
    assert result["score"] >= 75
    assert result["tier"] == "strong"
    assert result["title_in_family"] is True


def test_partial_match_is_good_or_weak_not_invented():
    result = score_job(JAVA_RESUME, JD_GOOD_PARTIAL, "Backend Software Engineer")
    assert result["score"] < 75
    joined_match = " ".join(result["matched_requirements"]).lower()
    assert "cobol" not in joined_match
    assert "apex" not in joined_match


def test_android_is_weak():
    result = score_job(JAVA_RESUME, JD_WEAK_ANDROID, "Android Engineer")
    assert result["tier"] == "weak"
    assert result["score"] < 50
    assert result["title_in_family"] is False


def test_keyword_trap_is_not_strong():
    """Same Java keywords, wrong title — must not become strong."""
    trapped = score_job(JAVA_RESUME, JD_KEYWORD_TRAP, "Android Intern")
    honest = score_job(JAVA_RESUME, JD_STRONG_JAVA, "Java Developer")
    assert honest["score"] >= 75
    assert trapped["score"] <= 49
    assert trapped["tier"] == "weak"
    assert trapped["title_in_family"] is False


def test_data_scientist_capped_weak():
    result = score_job(JAVA_RESUME, JD_DATA_SCIENTIST, "Data Scientist")
    assert result["score"] <= 49
    assert result["tier"] == "weak"


def test_no_heading_still_extracts():
    result = score_job(JAVA_RESUME, JD_NO_HEADING, "Java Software Engineer")
    assert result["scoring_status"] == "scored"
    assert result["score"] >= 50
    assert result["matched_requirements"]


def test_needs_manual_when_no_requirements():
    result = score_job(JAVA_RESUME, JD_NEEDS_MANUAL, "Java Developer")
    assert result["scoring_status"] == "needs_manual"
    assert result["score"] == 0


def test_nice_to_have_weighs_less_than_core():
    result = score_job(JAVA_RESUME, JD_NICE_HEAVY, "Java Developer")
    assert result["tier"] in {"good", "strong"}
    assert result["score"] >= 50
    # Unmatched COBOL/Salesforce must not dominate a real Java core match
    assert result["score"] >= 70


def test_staff_title_capped():
    result = score_job(JAVA_RESUME, JD_STAFF, "Staff Software Engineer")
    assert result["score"] <= 49
    assert result["tier"] == "weak"


def test_intern_title_capped():
    result = score_job(JAVA_RESUME, JD_INTERN, "Software Engineer Intern")
    assert result["score"] <= 49
    assert result["tier"] == "weak"


def test_unrelated_stack_is_weak():
    result = score_job(JAVA_RESUME, JD_FRONTEND_COBOL, "Software Engineer")
    assert result["tier"] == "weak"
    assert result["score"] < 50


def test_title_family():
    assert title_in_family("Senior Java Developer") is True
    assert title_in_family("Backend Software Engineer") is True
    assert title_in_family("Android Engineer") is False
    assert title_in_family("Data Scientist") is False


def test_canonical_resume_from_work_experience():
    data = canonical_resume(
        {
            "personal_information": {"name": "Roopa"},
            "work_experience": [
                {
                    "job_title": "Junior Software Engineer",
                    "company": "Cognizant",
                    "responsibilities_and_achievements": ["Built Spring Boot REST APIs"],
                }
            ],
            "skills": {"backend": ["Java", "Spring Boot"]},
        }
    )
    assert data["name"] == "Roopa"
    assert data["roles"][0]["title"] == "Junior Software Engineer"
    assert "Java" in data["skills"]
    assert "Spring Boot" in data["skills"]
