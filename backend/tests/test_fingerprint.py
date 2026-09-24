from app.jobs.fingerprint import canonical_url, fingerprint, is_linkedin, norm_name


def test_canonical_url_strips_tracking():
    left = canonical_url("https://WWW.Example.com/jobs/1?utm_source=x&gh_src=abc#top")
    right = canonical_url("https://example.com/jobs/1")
    assert left == right


def test_linkedin_detect():
    assert is_linkedin("https://www.linkedin.com/jobs/view/1")
    assert not is_linkedin("https://boards.greenhouse.io/acme/jobs/1")


def test_same_company_title_location_same_fingerprint():
    a = fingerprint("Java Developer", "Acme Inc.", "New York", "")
    b = fingerprint("Java Developer", "Acme", "New York", "")
    assert norm_name("Acme Inc.") == "acme"
    assert a == b
