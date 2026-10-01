"""Deterministic reports with source declarations on every surface."""
import json

def banner(result):
    sources = result["provenance"]
    return "Data provenance: " + ("; ".join(f"{s['file']}: {s['label']} ({s['count']} records)" for s in sources) if sources else "no inputs, zero records")

def render(result, format):
    if format == "json":
        return json.dumps({"provenance_banner": banner(result), **result}, ensure_ascii=False, sort_keys=True, indent=2)+"\n"
    if format != "md":
        raise ValueError("format: expected md or json")
    lines = ["# KOML Unknowns Register", "", banner(result), "", f"As of: {result['as_of']}", "", result["honesty"], "", "## Counts", ""]
    lines += [f"- {key}: {value}" for key,value in result["metrics"].items()]
    lines += ["", "## Traceable findings", ""]
    lines += [f"- {key}: {', '.join(result[key]) or '(none)'}" for key in ("unanswered_ids", "blocking_ids", "overdue_ids")]
    lines += ["", "## Decisions", ""]
    lines += [f"- {d['decision']}: unanswered {', '.join(d['unanswered_ids'])}; blocking {', '.join(d['blocking_ids']) or '(none)'}" for d in result["decisions"]]
    return "\n".join(lines)+"\n"
