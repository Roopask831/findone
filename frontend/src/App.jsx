import { useEffect, useState } from "react";

const API_KEY = import.meta.env.VITE_FINDONE_KEY || "change-me-local";

export default function App() {
  const [status, setStatus] = useState(null);
  const [current, setCurrent] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [jobFilter, setJobFilter] = useState("all");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [scoreResult, setScoreResult] = useState(null);

  async function onScore(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    const form = event.target;
    const response = await fetch("/api/score", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: form.job_title.value,
        jd_text: form.jd_text.value,
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      setError(payload.detail ? JSON.stringify(payload.detail) : "Score failed");
      return;
    }
    setScoreResult(payload);
  }

  async function load() {
    const statusResp = await fetch("/api/status");
    setStatus(await statusResp.json());
    const resumeResp = await fetch("/api/resumes/current");
    if (resumeResp.ok) {
      setCurrent(await resumeResp.json());
    } else {
      setCurrent(null);
    }
    const jobsResp = await fetch("/api/jobs");
    if (jobsResp.ok) {
      setJobs(await jobsResp.json());
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

  async function onImportJobs(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    const file = event.target.job_pool.files[0];
    if (!file) {
      setError("Choose a job_pool JSON file");
      return;
    }
    let parsed;
    try {
      parsed = JSON.parse(await file.text());
    } catch {
      setError("Invalid JSON file");
      return;
    }
    const jobsList = Array.isArray(parsed) ? parsed : parsed.jobs;
    if (!Array.isArray(jobsList)) {
      setError("JSON must be a list of jobs or { jobs: [...] }");
      return;
    }
    const response = await fetch("/api/jobs/import", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-FindOne-Key": API_KEY,
      },
      body: JSON.stringify({ jobs: jobsList }),
    });
    const payload = await response.json();
    if (!response.ok) {
      setError(payload.detail ? JSON.stringify(payload.detail) : "Import failed");
      return;
    }
    setMessage(
      `Imported ${payload.created} new, ${payload.updated} updated · queued ${payload.queued} · skipped ${payload.skipped}`,
    );
    await load();
  }

  const running = status?.running;
  const clockOff = status && !status.enforce_work_window;
  const visibleJobs =
    jobFilter === "all" ? jobs : jobs.filter((job) => job.status === jobFilter);

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
          <h2>Import job pool</h2>
          <p>
            Upload a JSON file with a <code>jobs</code> list (see{" "}
            <code>sample-data/job_pool.example.json</code>). Each job is scored and stored.
          </p>
          <form onSubmit={onImportJobs}>
            <label htmlFor="job_pool">job_pool.json</label>
            <input id="job_pool" name="job_pool" type="file" accept=".json,application/json" required />
            <button type="submit">Import and score</button>
          </form>

          <h2>Jobs ({visibleJobs.length})</h2>
          {status?.counts && (
            <p>
              Queued {status.counts.queue} · Skipped {status.counts.skipped} · On hold{" "}
              {status.counts.on_hold}
            </p>
          )}
          <label htmlFor="job_filter">Filter status</label>
          <select
            id="job_filter"
            value={jobFilter}
            onChange={(event) => setJobFilter(event.target.value)}
          >
            <option value="all">All</option>
            <option value="Queued">Queued</option>
            <option value="Skipped">Skipped</option>
            <option value="On hold">On hold</option>
          </select>
          {visibleJobs.length === 0 ? (
            <p>No jobs in this filter yet.</p>
          ) : (
            <table className="jobs">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Company</th>
                  <th>Location</th>
                  <th>Score</th>
                  <th>Tier</th>
                  <th>Status</th>
                  <th>View</th>
                </tr>
              </thead>
              <tbody>
                {visibleJobs.map((job) => (
                  <tr key={job.job_id}>
                    <td>
                      <a href={`/jobs/${encodeURIComponent(job.job_id)}`}>{job.title}</a>
                    </td>
                    <td>{job.company}</td>
                    <td>{job.location}</td>
                    <td>{job.score}</td>
                    <td>{job.tier}</td>
                    <td>
                      {job.status}
                      {job.hold_reason ? ` (${job.hold_reason})` : ""}
                    </td>
                    <td>
                      <a href={`/jobs/${encodeURIComponent(job.job_id)}`}>View</a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <p>View opens the stored listing in FindOne. Sample apply URLs are not real company pages.</p>

          <h2>Score a job description</h2>
          <p>Paste a title and JD. Scoring uses your saved resume only — no AI API.</p>
          <form onSubmit={onScore}>
            <label htmlFor="job_title">Job title</label>
            <input id="job_title" name="job_title" placeholder="Java Developer" />
            <label htmlFor="jd_text">Job description</label>
            <textarea id="jd_text" name="jd_text" rows="12" required />
            <button type="submit">Score this job</button>
          </form>
          {scoreResult && (
            <pre>
              {scoreResult.tier} · {scoreResult.score} / 100 · {scoreResult.scoring_status}
              {"\n"}
              {scoreResult.reasoning}
              {"\n\nMatched:\n"}
              {(scoreResult.matched_requirements || []).join("\n") || "(none)"}
              {"\n\nGaps:\n"}
              {(scoreResult.gaps || []).join("\n") || "(none)"}
            </pre>
          )}
          <h2>Saved cover letter</h2>
          <pre>{current.cover_letter_template}</pre>
          <h2>Saved resume text</h2>
          <pre>{current.resume_text}</pre>
        </>
      )}
    </main>
  );
}
