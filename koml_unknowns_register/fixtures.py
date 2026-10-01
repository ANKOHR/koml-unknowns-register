"""Synthetic fixtures with a manually specified block design; no randomness."""
import json
from pathlib import Path

AS_OF = "2026-09-30"

def fixture_records():
    records = []
    for i in range(1, 201):
        status = "open" if i <= 100 else "answered" if i <= 160 else "deferred"
        records.append({"id": f"Q{i:03}", "question": f"What evidence settles question {i}?",
                        "decision": f"Decision {(i-1)//20+1:02}", "status": status,
                        "blocking": i <= 40 or i > 180, "created": "2026-09-01",
                        "due": "2026-09-20" if i <= 60 or 161 <= i <= 180 else "2026-10-10",
                        "answer": "Evidence recorded" if status == "answered" else "", "synthetic": True})
    return records

def expectations():
    # Hand calculation: 100 open + 40 deferred, 40 + 20 blockers, 60 + 20 overdue.
    return {"synthetic": True, "label": "SYNTHETIC hand-computed expectations",
            "metrics": {"total": 200, "open": 100, "answered": 60, "deferred": 40,
                        "unanswered": 140, "blocking_unanswered": 60, "overdue_unanswered": 80, "decisions_affected": 7},
            "unanswered_ids": [f"Q{i:03}" for i in list(range(1,101))+list(range(161,201))],
            "blocking_ids": [f"Q{i:03}" for i in list(range(1,41))+list(range(181,201))],
            "overdue_ids": [f"Q{i:03}" for i in list(range(1,61))+list(range(161,181))]}

def generate(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    payload = {"synthetic": True, "label": "SYNTHETIC fixture data", "as_of": AS_OF, "records": fixture_records()}
    for name, value in (("unknowns.json", payload), ("expectations.json", expectations())):
        (out/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (out/"LABEL.md").write_text("<!-- SYNTHETIC -->\nAll data in this folder are synthetic fixtures. JSON has explicit labels because JSON does not support comments.\n", encoding="utf-8")
