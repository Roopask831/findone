import json

from tests.fixtures_jds import JAVA_RESUME, JD_NEEDS_MANUAL, JD_STRONG_JAVA


def _upload_resume(client):
    test_client, _settings = client
    response = test_client.post(
        "/api/resumes",
        headers={"X-FindOne-Key": "test-key"},
        data={
            "resume_json": json.dumps(JAVA_RESUME),
            "cover_letter_template": "Dear {company}",
        },
        files={"pdf": ("resume.pdf", b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n", "application/pdf")},
    )
    assert response.status_code == 201, response.text
    return test_client


def test_import_requires_resume(client):
    test_client, _settings = client
    response = test_client.post(
        "/api/jobs/import",
        headers={"X-FindOne-Key": "test-key"},
        json={"jobs": [{"title": "Java Developer", "jd_text": JD_STRONG_JAVA}]},
    )
    assert response.status_code == 400


def test_import_scores_and_filters(client):
    test_client = _upload_resume(client)
    payload = {
        "jobs": [
            {
                "job_id": "java-1",
                "title": "Java Developer",
                "company": "Acme",
                "location": "US",
                "apply_url": "https://boards.greenhouse.io/acme/jobs/1",
                "jd_text": JD_STRONG_JAVA,
            },
            {
                "job_id": "android-1",
                "title": "Android Intern",
                "company": "PhoneCo",
                "apply_url": "https://jobs.lever.co/phoneco/x",
                "jd_text": JD_STRONG_JAVA,
            },
            {
                "job_id": "li-1",
                "title": "Backend Software Engineer",
                "company": "LinkedCorp",
                "apply_url": "https://www.linkedin.com/jobs/view/99",
                "jd_text": JD_STRONG_JAVA,
            },
            {
                "job_id": "vague-1",
                "title": "Java Developer",
                "company": "VagueCo",
                "apply_url": "https://boards.greenhouse.io/vague/jobs/9",
                "jd_text": JD_NEEDS_MANUAL,
            },
        ]
    }
    imported = test_client.post(
        "/api/jobs/import",
        headers={"X-FindOne-Key": "test-key"},
        json=payload,
    )
    assert imported.status_code == 200, imported.text
    stats = imported.json()
    assert stats["created"] == 4
    assert stats["queued"] >= 1
    assert stats["skipped"] >= 2
    assert stats["on_hold"] >= 1

    jobs = test_client.get("/api/jobs").json()
    assert len(jobs) == 4
    by_id = {job["job_id"]: job for job in jobs}
    assert by_id["java-1"]["status"] == "Queued"
    assert by_id["java-1"]["tier"] == "strong"
    assert by_id["android-1"]["status"] == "Skipped"
    assert by_id["android-1"]["hold_reason"] == "title_cap"
    assert by_id["li-1"]["hold_reason"] == "linkedin"
    assert by_id["vague-1"]["status"] == "On hold"
    assert by_id["vague-1"]["hold_reason"] == "needs_manual"

    queued = test_client.get("/api/jobs", params={"status": "Queued"}).json()
    assert all(job["status"] == "Queued" for job in queued)
    assert test_client.get("/api/jobs/java-1").json()["jd_text"]
    assert test_client.get("/api/jobs/missing").status_code == 404
    page = test_client.get("/jobs/java-1")
    assert page.status_code == 200
    assert "Java Developer" in page.text
    assert "Job description" in page.text
    assert test_client.get("/jobs/missing").status_code == 404

    again = test_client.post(
        "/api/jobs/import",
        headers={"X-FindOne-Key": "test-key"},
        json=payload,
    )
    assert again.json()["created"] == 0
    assert again.json()["updated"] == 4
    assert len(test_client.get("/api/jobs").json()) == 4
