from datetime import datetime

from app.config import clock_in_work_window, operations_allowed
from app.resume_text import flatten_resume
from app.scheduler import next_poll_at


def test_flatten_includes_roles_skills_and_education():
    text = flatten_resume(
        {
            "name": "Alex Java",
            "email": "alex@example.com",
            "roles": [
                {
                    "title": "Java Developer",
                    "company": "Acme",
                    "start_date": "2022-01",
                    "end_date": "Present",
                    "bullets": ["Built Spring Boot REST APIs"],
                }
            ],
            "skills": ["Java", "Spring Boot"],
            "education": [{"school": "State University", "degree": "B.S."}],
            "certifications": ["AWS CCP"],
        }
    )
    assert "Alex Java" in text
    assert "Java Developer" in text
    assert "Built Spring Boot REST APIs" in text
    assert "Spring Boot" in text
    assert "State University" in text
    assert "AWS CCP" in text


def test_flatten_does_not_invent_skills():
    text = flatten_resume(
        {
            "roles": [
                {
                    "title": "Backend Developer",
                    "company": "Co",
                    "start_date": "2020",
                    "end_date": "2021",
                    "bullets": ["Wrote services"],
                }
            ],
            "skills": ["Java"],
        }
    )
    assert "Kafka" not in text
    assert "Java" in text


def test_work_window_boundaries():
    profile = {"work_start": "06:00", "work_end": "15:30", "enforce_work_window": True}
    morning = datetime(2026, 9, 17, 6, 0)
    afternoon = datetime(2026, 9, 17, 15, 30)
    evening = datetime(2026, 9, 17, 16, 0)
    early = datetime(2026, 9, 17, 5, 59)
    assert clock_in_work_window(morning, profile)
    assert clock_in_work_window(afternoon, profile)
    assert not clock_in_work_window(evening, profile)
    assert not clock_in_work_window(early, profile)
    assert not operations_allowed(evening, profile)


def test_clock_disabled_allows_any_hour():
    profile = {"work_start": "06:00", "work_end": "15:30", "enforce_work_window": False}
    evening = datetime(2026, 9, 17, 22, 0)
    assert not clock_in_work_window(evening, profile)
    assert operations_allowed(evening, profile)


def test_next_poll_aligns_to_window_when_enforced():
    profile = {
        "work_start": "06:00",
        "work_end": "15:30",
        "poll_minutes": 20,
        "enforce_work_window": True,
    }
    before = datetime(2026, 9, 17, 5, 50)
    mid = datetime(2026, 9, 17, 6, 5)
    late = datetime(2026, 9, 17, 15, 10)
    last_slot = datetime(2026, 9, 17, 15, 20)
    after = datetime(2026, 9, 17, 16, 0)
    assert next_poll_at(before, profile) == datetime(2026, 9, 17, 6, 0)
    assert next_poll_at(mid, profile) == datetime(2026, 9, 17, 6, 20)
    assert next_poll_at(late, profile) == datetime(2026, 9, 17, 15, 20)
    assert next_poll_at(last_slot, profile) == datetime(2026, 9, 18, 6, 0)
    assert next_poll_at(after, profile) == datetime(2026, 9, 18, 6, 0)


def test_next_poll_without_clock_is_interval_from_now():
    profile = {
        "work_start": "06:00",
        "work_end": "15:30",
        "poll_minutes": 20,
        "enforce_work_window": False,
    }
    now = datetime(2026, 9, 17, 22, 0)
    assert next_poll_at(now, profile) == datetime(2026, 9, 17, 22, 20)
