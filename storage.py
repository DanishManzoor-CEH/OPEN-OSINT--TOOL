import json
import re
from datetime import datetime, timezone
from pathlib import Path

DATA = Path("data")
HISTORY = DATA / "history"
REPORTS = DATA / "reports"
HISTORY.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

def slug(value):
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip())[:60].strip("-") or "item"

def save_investigation(prompt, result):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    path = HISTORY / f"{stamp}-{slug(prompt)}.json"
    path.write_text(json.dumps({"created_at": datetime.now(timezone.utc).isoformat(), "prompt": prompt, "result": result}, ensure_ascii=False, indent=2), encoding="utf-8")
    return path

def list_investigations():
    return sorted(HISTORY.glob("*.json"), reverse=True)

def load_investigation(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def save_report(title, content):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    path = REPORTS / f"{stamp}-{slug(title)}.md"
    path.write_text(content, encoding="utf-8")
    return path

def list_reports():
    return sorted(REPORTS.glob("*.md"), reverse=True)

def read_report(path):
    return Path(path).read_text(encoding="utf-8")
