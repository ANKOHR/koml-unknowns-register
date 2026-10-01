"""Pure validation and aggregation. No savings or predictions are estimated."""
from datetime import date

class SchemaError(ValueError):
    """Input does not conform to the documented schema."""

def validate_record(record, as_of):
    fields = {"id", "question", "decision", "status", "blocking", "created", "due", "answer", "synthetic"}
    if not isinstance(record, dict):
        raise SchemaError("record: expected object")
    if set(record) != fields:
        raise SchemaError(f"fields: missing {sorted(fields - set(record))}, unknown {sorted(set(record) - fields)}")
    for field in ("id", "question", "decision", "answer"):
        if not isinstance(record[field], str) or len(record[field]) > 100000 or (field != "answer" and not record[field].strip()):
            raise SchemaError(f"{field}: expected nonempty text up to 100000 characters (answer may be empty)")
        if "\u2014" in record[field]:
            raise SchemaError(f"{field}: em dash is forbidden; use a hyphen")
    for field in ("blocking", "synthetic"):
        if type(record[field]) is not bool:
            raise SchemaError(f"{field}: expected boolean")
    if not isinstance(record["status"], str) or record["status"] not in ("open", "answered", "deferred"):
        raise SchemaError("status: expected open, answered, or deferred")
    if (record["status"] == "answered") != bool(record["answer"].strip()):
        raise SchemaError("answer: required only for answered status")
    for field in ("created", "due"):
        value = record[field]
        if field == "due" and value is None:
            continue
        try:
            parsed = date.fromisoformat(value)
            if parsed.isoformat() != value:
                raise ValueError()
        except (ValueError, TypeError):
            raise SchemaError(f"{field}: expected YYYY-MM-DD") from None
        if field == "created" and parsed > as_of:
            raise SchemaError("created: future creation date")
    if record["due"] is not None and record["due"] < record["created"]:
        raise SchemaError("due: precedes created")
    return dict(record)

def aggregate(records, as_of, sources):
    """Count declared facts, including deferred questions as unanswered."""
    seen = set()
    validated = []
    for record in records:
        r = validate_record(record, as_of)
        if r["id"] in seen:
            raise SchemaError(f"id: duplicate {r['id']!r}")
        seen.add(r["id"])
        validated.append(r)
    validated.sort(key=lambda r: r["id"])
    unanswered = [r for r in validated if r["status"] != "answered"]
    blocking = [r for r in unanswered if r["blocking"]]
    overdue = [r for r in unanswered if r["due"] is not None and r["due"] < as_of.isoformat()]
    metrics = {"total": len(validated), "open": sum(r["status"] == "open" for r in validated),
               "answered": len(validated)-len(unanswered), "deferred": sum(r["status"] == "deferred" for r in validated),
               "unanswered": len(unanswered), "blocking_unanswered": len(blocking), "overdue_unanswered": len(overdue),
               "decisions_affected": len({r["decision"] for r in unanswered})}
    decisions = [{"decision": d, "unanswered_ids": [r["id"] for r in unanswered if r["decision"] == d],
                  "blocking_ids": [r["id"] for r in blocking if r["decision"] == d]}
                 for d in sorted({r["decision"] for r in unanswered})]
    return {"as_of": as_of.isoformat(), "provenance": sorted(sources, key=lambda s: s["file"]),
            "metrics": metrics, "unanswered_ids": [r["id"] for r in unanswered],
            "blocking_ids": [r["id"] for r in blocking], "overdue_ids": [r["id"] for r in overdue],
            "records": validated, "decisions": decisions,
            "honesty": "Counts computed from supplied inputs only. Real labels are user declarations, not independently verified. Time and money saved are unmeasured and are not reported."}
