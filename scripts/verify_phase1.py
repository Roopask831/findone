import json
import urllib.error
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[1]
print(urllib.request.urlopen("http://127.0.0.1:8000/api/status").read().decode())

pdf_bytes = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
resume = (root / "sample-data" / "master_resume.example.json").read_text(encoding="utf-8")
template = (root / "sample-data" / "cover_letter.template.txt").read_text(encoding="utf-8")
boundary = "----FindOneBoundary"


def part(name: str, value: bytes, filename: str | None = None, ctype: str | None = None) -> bytes:
    disp = f'Content-Disposition: form-data; name="{name}"'
    if filename:
        disp += f'; filename="{filename}"'
    headers = [disp]
    if ctype:
        headers.append(f"Content-Type: {ctype}")
    return ("\r\n".join(headers) + "\r\n\r\n").encode() + value + b"\r\n"


chunks = [
    part("resume_json", resume.encode()),
    part("cover_letter_template", template.encode()),
    part("label", b"master"),
    part("pdf", pdf_bytes, "resume.pdf", "application/pdf"),
]
sep = b"--" + boundary.encode() + b"\r\n"
body = sep + (b"--" + boundary.encode() + b"\r\n").join(chunks) + b"--" + boundary.encode() + b"--\r\n"
req = urllib.request.Request(
    "http://127.0.0.1:8000/api/resumes",
    data=body,
    method="POST",
    headers={
        "X-FindOne-Key": "change-me-local",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    },
)
try:
    created = urllib.request.urlopen(req).read().decode()
    print(created[:900])
except urllib.error.HTTPError as exc:
    print(exc.read().decode())
    raise

current = json.loads(urllib.request.urlopen("http://127.0.0.1:8000/api/resumes/current").read().decode())
print("current id", current["id"])
print("has Java Developer", "Java Developer" in current["resume_text"])
print("pdf path", current["master_pdf_path"])
frontend = urllib.request.urlopen("http://127.0.0.1:5173").read().decode()
print("frontend title", "FindOne" in frontend)
