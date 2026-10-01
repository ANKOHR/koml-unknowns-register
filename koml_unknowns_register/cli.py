"""Local file CLI. All writes use atomic replacement."""
import argparse
from datetime import date
import json
from pathlib import Path
import os
import tempfile
import sys
from .core import SchemaError, aggregate, validate_record
from .fixtures import generate
from .report import render, banner

class InputError(ValueError):
    pass

def atomic_write(path, text):
    path = Path(path)
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as f:
            temporary = f.name
            f.write(text)
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)

def load_inputs(directory, override=None):
    directory = Path(directory)
    if not directory.is_dir():
        raise InputError(f"MissingInput: {directory}; use kur fixtures --out demo or supply an input directory")
    records, sources = [], []
    try:
        as_of = date.fromisoformat(override) if override else None
        if override and as_of.isoformat() != override:
            raise ValueError()
    except (ValueError, TypeError):
        raise InputError("SchemaError: --as-of: expected YYYY-MM-DD") from None
    for path in sorted(directory.iterdir()):
        if path.name in ("expectations.json", "LABEL.md") or path.is_dir():
            continue
        if path.suffix != ".json":
            raise InputError(f"SchemaError: {path.name}: line 1: format: only JSON input files supported")
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise InputError(f"ParseError: {path.name}: line {e.lineno}: {e.msg}") from None
        except UnicodeError:
            raise InputError(f"ParseError: {path.name}: line 1: expected UTF-8") from None
        try:
            if not isinstance(obj, dict) or set(obj) != {"synthetic", "label", "as_of", "records"}:
                raise SchemaError("fields: expected synthetic, label, as_of, records")
            if type(obj["synthetic"]) is not bool or not isinstance(obj["records"], list):
                raise SchemaError("synthetic/records: expected boolean/list")
            expected_label = "SYNTHETIC fixture data" if obj["synthetic"] else "REAL user-entered data"
            if obj["label"] != expected_label:
                raise SchemaError(f"label: expected {expected_label}")
            declared = date.fromisoformat(obj["as_of"])
            if declared.isoformat() != obj["as_of"]:
                raise SchemaError("as_of: expected YYYY-MM-DD")
            if as_of is None:
                as_of = declared
            if not override and declared != as_of:
                raise SchemaError("as_of: all files must agree or supply --as-of")
            for r in obj["records"]:
                validate_record(r, as_of)
                if r["synthetic"] != obj["synthetic"]:
                    raise SchemaError("synthetic: record/file declaration mismatch")
            records.extend(obj["records"])
            sources.append({"file": path.name, "label": expected_label, "synthetic": obj["synthetic"], "count": len(obj["records"])})
        except (ValueError, TypeError) as e:
            raise InputError(f"SchemaError: {path.name}: line 1: {e}") from None
    try:
        return aggregate(records, as_of or date(2026,9,30), sources)
    except SchemaError as e:
        raise InputError(f"SchemaError: {directory}: line 1: {e}") from None

def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Track declared unknowns affecting decisions. Local files only.")
    parser.add_argument("--state", default=".kur/results.json", help="local cached result path")
    sub = parser.add_subparsers(dest="command", required=True)
    f = sub.add_parser("fixtures", help="generate 200 labelled synthetic records", epilog="Example: kur fixtures --out demo")
    f.add_argument("--out", required=True)
    r = sub.add_parser("run", help="validate input and compute register", epilog="Example: kur run --input demo")
    r.add_argument("--input", required=True)
    r.add_argument("--as-of", help="explicit YYYY-MM-DD reporting date")
    rep = sub.add_parser("report", help="render cached results with provenance", epilog="Example: kur report --format md")
    rep.add_argument("--format", choices=("md", "json"), default="md")
    rep.add_argument("--out", help="atomically write report to file")
    q = sub.add_parser("questions", help="list unanswered questions from latest run", epilog="Example: kur questions --blocking")
    q.add_argument("--blocking", action="store_true")
    q.add_argument("--decision", help="exact decision name")
    sub.add_parser("decisions", help="list decisions affected by unanswered questions", epilog="Example: kur decisions")
    args = parser.parse_args(argv)
    try:
        if args.command == "fixtures":
            generate(args.out)
            print("SYNTHETIC: generated 200 labelled records; no real trial results.")
        elif args.command == "run":
            result = load_inputs(args.input, args.as_of)
            atomic_write(args.state, render(result, "json"))
            print(banner(result))
            print(f"Computed {result['metrics']['total']} records. Savings unmeasured and not reported.")
        else:
            if not Path(args.state).is_file():
                raise InputError(f"MissingInput: {args.state}; run kur run --input <dir> first")
            try:
                cached = json.loads(Path(args.state).read_text(encoding="utf-8"))
                sources = cached["provenance"]
                if not isinstance(sources, list) or any(not isinstance(s, dict) or set(s) != {"file", "label", "synthetic", "count"} for s in sources):
                    raise ValueError("provenance: invalid cached sources")
                result = aggregate(cached["records"], date.fromisoformat(cached["as_of"]), sources)
                if sum(s["count"] for s in sources) != result["metrics"]["total"]:
                    raise ValueError("provenance: count mismatch")
            except (ValueError, KeyError, TypeError) as e:
                raise InputError(f"StateError: {args.state}: invalid cached result; rerun kur run: {e}") from None
            if args.command == "report":
                output = render(result, args.format)
                if args.out:
                    atomic_write(args.out, output)
                else:
                    print(output, end="")
            else:
                print(banner(result))
                if args.command == "decisions":
                    data = result["decisions"]
                else:
                    data = [r for r in result["records"] if r["status"] != "answered" and (not args.blocking or r["blocking"]) and (args.decision is None or r["decision"] == args.decision)]
                print(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except (InputError, SchemaError, ValueError, OSError) as e:
        category = "FileError" if isinstance(e, OSError) else "InputError"
        message = str(e).replace(chr(0x2014), "-")
        parser.exit(2, f"{category}: {message}\n")

if __name__ == "__main__":
    main()
