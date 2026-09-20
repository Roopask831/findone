"""Render mermaid blocks from scope.md via mermaid.ink and rewrite markdown with images."""
from __future__ import annotations

import base64
import json
import re
import time
import urllib.error
import urllib.request
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "scope.md"
OUT = ROOT / "diagrams"

NAMES = [
    "10-system-context",
    "11-container-c4",
    "12-component-design",
    "13-job-lifecycle",
    "14-decision-tree",
    "15-discovery-sequence",
    "16-apply-sequence",
    "17-scheduler",
    "18-data-model-er",
]

ALTS = {
    "10-system-context": "System context",
    "11-container-c4": "Container view (C4)",
    "12-component-design": "Component design",
    "13-job-lifecycle": "Job lifecycle",
    "14-decision-tree": "Decision tree: skip vs hold vs submit",
    "15-discovery-sequence": "Discovery cycle sequence",
    "16-apply-sequence": "Apply one job sequence",
    "17-scheduler": "Scheduler logic",
    "18-data-model-er": "Data model (ER)",
}


def fetch_svg(mermaid: str) -> bytes:
    state = json.dumps(
        {"code": mermaid.strip(), "mermaid": {"theme": "default"}},
        separators=(",", ":"),
    )
    token = base64.urlsafe_b64encode(zlib.compress(state.encode("utf-8"), 9)).decode("ascii")
    url = "https://mermaid.ink/svg/pako:" + token
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 FindOnePlan/1.0"})
    last_err: Exception | None = None
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = resp.read()
            if b"<svg" not in data[:200]:
                raise RuntimeError("response was not SVG")
            return data
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            last_err = exc
            wait = 2 ** attempt
            print(f"  retry {attempt + 1} after {wait}s ({exc})")
            time.sleep(wait)
    raise RuntimeError(f"failed after retries: {last_err}") from last_err


def main() -> None:
    OUT.mkdir(exist_ok=True)
    text = MD.read_text(encoding="utf-8")
    pattern = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)
    blocks = pattern.findall(text)
    if len(blocks) != len(NAMES):
        raise SystemExit(f"expected {len(NAMES)} mermaid blocks, found {len(blocks)}")

    for name, mermaid in zip(NAMES, blocks):
        svg_path = OUT / f"{name}.svg"
        if svg_path.exists() and b"<svg" in svg_path.read_bytes()[:200]:
            print(f"exists {name}")
            continue
        print(f"rendering {name} ...")
        svg_path.write_bytes(fetch_svg(mermaid))
        time.sleep(1)

    def replace(match: re.Match[str], counter=[0]) -> str:
        i = counter[0]
        counter[0] += 1
        name = NAMES[i]
        return f"![{ALTS[name]}](diagrams/{name}.svg)\n"

    MD.write_text(pattern.sub(replace, text), encoding="utf-8")
    print("updated", MD)


if __name__ == "__main__":
    main()
