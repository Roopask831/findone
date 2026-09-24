import json
from pathlib import Path

MIN_PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"

SAMPLE = {
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
    "skills": ["Java", "Spring Boot", "REST"],
    "education": [{"school": "State University", "degree": "B.S.", "field": "CS"}],
    "certifications": ["AWS CCP"],
}


def test_status_ok(client):
    test_client, _settings = client
    response = test_client.get("/api/status")
    assert response.status_code == 200
    body = response.json()
    assert body["product"] == "FindOne"
    assert body["work_start"] == "06:00"
    assert body["work_end"] == "15:30"
    assert body["poll_minutes"] == 20
    assert body["has_current_resume"] is False
    assert body["enforce_work_window"] is False
    assert body["running"] is True
    assert body["database_ready"] is True
    assert body["next_poll"]


def test_hello(client):
    test_client, _settings = client
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json()["product"] == "FindOne"


def test_current_resume_404_when_empty(client):
    test_client, _settings = client
    response = test_client.get("/api/resumes/current")
    assert response.status_code == 404


def test_upload_requires_key(client):
    test_client, _settings = client
    response = test_client.post(
        "/api/resumes",
        data={"resume_json": json.dumps(SAMPLE)},
        files={"pdf": ("resume.pdf", MIN_PDF, "application/pdf")},
    )
    assert response.status_code == 401


def test_upload_and_get_current_round_trip(client):
    test_client, settings = client
    template = "Dear {company} Hiring Team,\nI am applying for {job_title}.\n"
    response = test_client.post(
        "/api/resumes",
        headers={"X-FindOne-Key": "test-key"},
        data={
            "resume_json": json.dumps(SAMPLE),
            "cover_letter_template": template,
            "label": "master",
        },
        files={"pdf": ("resume.pdf", MIN_PDF, "application/pdf")},
    )
    assert response.status_code == 201, response.text
    created = response.json()
    assert created["is_current"] is True
    assert "Java Developer" in created["resume_text"]
    assert "Built Spring Boot REST APIs" in created["resume_text"]
    assert created["cover_letter_template"].startswith("Dear")
    assert created["resume_json"]["skills"] == SAMPLE["skills"]

    stored = Path(settings.data_dir) / "resumes" / str(created["id"]) / "master.pdf"
    current = Path(settings.data_dir) / "resumes" / "master.pdf"
    assert stored.is_file()
    assert current.is_file()
    assert stored.read_bytes().startswith(b"%PDF")
    assert current.read_bytes() == stored.read_bytes()

    current_resp = test_client.get("/api/resumes/current")
    assert current_resp.status_code == 200
    body = current_resp.json()
    assert body["id"] == created["id"]
    assert body["resume_text"] == created["resume_text"]

    status_resp = test_client.get("/api/status")
    assert status_resp.json()["has_current_resume"] is True


def test_reject_non_pdf(client):
    test_client, _settings = client
    response = test_client.post(
        "/api/resumes",
        headers={"X-FindOne-Key": "test-key"},
        data={"resume_json": json.dumps(SAMPLE)},
        files={"pdf": ("resume.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 400


def test_reject_missing_cover_letter(client):
    test_client, _settings = client
    response = test_client.post(
        "/api/resumes",
        headers={"X-FindOne-Key": "test-key"},
        data={"resume_json": json.dumps(SAMPLE)},
        files={"pdf": ("resume.pdf", MIN_PDF, "application/pdf")},
    )
    assert response.status_code == 400


def test_reject_invalid_json(client):
    test_client, _settings = client
    response = test_client.post(
        "/api/resumes",
        headers={"X-FindOne-Key": "test-key"},
        data={"resume_json": "{not-json"},
        files={"pdf": ("resume.pdf", MIN_PDF, "application/pdf")},
    )
    assert response.status_code == 400


def test_score_endpoint_uses_current_resume(client):
    test_client, _settings = client
    uploaded = test_client.post(
        "/api/resumes",
        headers={"X-FindOne-Key": "test-key"},
        data={
            "resume_json": json.dumps(SAMPLE),
            "cover_letter_template": "Dear {company}",
        },
        files={"pdf": ("resume.pdf", MIN_PDF, "application/pdf")},
    )
    assert uploaded.status_code == 201, uploaded.text
    response = test_client.post(
        "/api/score",
        json={
            "title": "Java Developer",
            "jd_text": (
                "Java Developer\n\nRequirements:\n"
                "- Professional experience with Java and Spring Boot REST APIs\n"
                "- Build backend services used by internal tools every day\n"
            ),
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["scoring_status"] == "scored"
    assert "tier" in body
    assert body["score"] >= 0
