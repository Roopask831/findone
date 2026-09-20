import { useEffect, useState } from "react";

const API_KEY = import.meta.env.VITE_FINDONE_KEY || "change-me-local";

export default function App() {
  const [status, setStatus] = useState(null);
  const [current, setCurrent] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function load() {
    const statusResp = await fetch("/api/status");
    setStatus(await statusResp.json());
    const resumeResp = await fetch("/api/resumes/current");
    if (resumeResp.ok) {
      setCurrent(await resumeResp.json());
    } else {
      setCurrent(null);
    }
  }

  useEffect(() => {
    load().catch((err) => setError(String(err)));
  }, []);

  async function onSubmit(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    const form = event.target;
    const body = new FormData();
    const jsonFile = form.resume_json_file.files[0];
    const jsonText = form.resume_json.value.trim();
    const letterFile = form.cover_letter_file.files[0];
    const letterText = form.cover_letter_template.value.trim();

    body.set("label", "master");
    body.set("pdf", form.pdf.files[0]);
    if (jsonFile) {
      body.set("resume_json_file", jsonFile);
    } else if (jsonText) {
      body.set("resume_json", jsonText);
    }
    if (letterFile) {
      body.set("cover_letter_file", letterFile);
    } else if (letterText) {
      body.set("cover_letter_template", letterText);
    }

    const response = await fetch("/api/resumes", {
      method: "POST",
      headers: { "X-FindOne-Key": API_KEY },
      body,
    });
    const payload = await response.json();
    if (!response.ok) {
      setError(payload.detail ? JSON.stringify(payload.detail) : "Upload failed");
      return;
    }
    setMessage(`Saved resume #${payload.id}`);
    await load();
  }

  const running = status?.running;
  const clockOff = status && !status.enforce_work_window;

  return (
    <main>
      <h1>FindOne</h1>
      <p>
        Upload your <strong>resume PDF</strong> and <strong>cover letter</strong>. JSON is optional
        if the PDF has selectable text.
      </p>
      {status && (
        <div className={`banner ${running ? "on" : "off"}`}>
          {clockOff
            ? "Always on — 6:00–15:30 clock is off until the product is complete"
            : running
              ? "Running window (6:00–15:30)"
              : "Outside work window"}{" "}
          · resume {status.has_current_resume ? "on file" : "not uploaded yet"}
        </div>
      )}

      <h2>API status</h2>
      <pre className="status-json">{status ? JSON.stringify(status, null, 2) : "Loading /api/status…"}</pre>

      <form onSubmit={onSubmit}>
        <label htmlFor="pdf">Resume PDF (required)</label>
        <input id="pdf" name="pdf" type="file" accept="application/pdf" required />

        <label htmlFor="cover_letter_file">Cover letter file (.txt) — or paste below</label>
        <input id="cover_letter_file" name="cover_letter_file" type="file" accept=".txt,text/plain" />

        <label htmlFor="cover_letter_template">Cover letter text</label>
        <textarea
          id="cover_letter_template"
          name="cover_letter_template"
          rows="10"
          placeholder="Paste your cover letter or template here if you are not uploading a .txt file."
        />

        <label htmlFor="resume_json_file">Structured resume JSON file (optional)</label>
        <input id="resume_json_file" name="resume_json_file" type="file" accept=".json,application/json" />

        <label htmlFor="resume_json">Or paste resume JSON (optional)</label>
        <textarea id="resume_json" name="resume_json" rows="8" placeholder='{"roles":[...],"skills":[...]}' />

        <button type="submit">Save resume and cover letter</button>
      </form>

      {error && <p className="error">{error}</p>}
      {message && <p className="ok">{message}</p>}

      {current && (
        <>
          <h2>Saved cover letter</h2>
          <pre>{current.cover_letter_template}</pre>
          <h2>Saved resume text</h2>
          <pre>{current.resume_text}</pre>
        </>
      )}
    </main>
  );
}
