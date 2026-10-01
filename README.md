# KOML Unknowns Register

`kur` explicitly tracks unanswered questions affecting decisions. It computes declared facts from local JSON files. It does not discover unknowns, verify answers, predict outcomes, or estimate savings. Python 3.10 or newer, CPU only, standard library runtime, no network calls or model calls.

## Hypothesis and acceptance

A deterministic register can reliably surface declared unanswered, blocking, and overdue questions. Acceptance: exact results on 200 planted synthetic records, zero false positives, reports in under five seconds, a working end-to-end demo, and adversarial validation. This validates computation, not the completeness or truth of a human's register.

## Quickstart

Install with existing local setuptools and pip (no network):

```powershell
python -m pip install --no-deps --no-build-isolation -e .
kur fixtures --out demo
kur run --input demo
kur report --format md
python -m pytest -q
```

If Windows does not put the user Scripts directory on PATH, add the Scripts directory printed by pip to PATH or use the module command below.

Without installation: `python -m koml_unknowns_register.cli` accepts the same arguments. On shells supporting `&&`, the demo is `kur fixtures --out demo && kur run --input demo && kur report --format md`.

Smallest hand-written version:

```powershell
kur run --input examples/five
kur report --format md
```

Those five records are synthetic: 3 unanswered, 1 blocking, 1 overdue, 2 answered, 1 affected decision. Run the 200-record demo again to restore its cached results.

## Input format

An input directory contains one or more UTF-8 JSON files, each with exactly these envelope keys:

```json
{
  "synthetic": false,
  "label": "REAL user-entered data",
  "as_of": "2026-09-30",
  "records": [{
    "id": "question-1",
    "question": "Has Henry verified the backup?",
    "decision": "Approve launch",
    "status": "open",
    "blocking": true,
    "created": "2026-09-01",
    "due": "2026-10-10",
    "answer": "",
    "synthetic": false
  }]
}
```

This README example is hypothetical, not real trial evidence. Set `synthetic: false` only for Henry's own data entered by him. A real label is a user declaration, not independent verification. Synthetic files require the label `SYNTHETIC fixture data` and true on every record. File and record declarations must agree. Reports name each source and its declared provenance, including mixed inputs.

All nine record fields are required; unknown fields are errors. Text fields accept Unicode and Windows paths (escape backslashes in JSON), up to 100000 characters. IDs, questions and decisions cannot be whitespace-only. IDs must be unique across all files. Status is exactly `open`, `answered`, or `deferred`. Only answered records require a nonblank answer; others require a blank answer. Boolean fields accept JSON booleans only. Money/amount fields, including negative amounts, are outside the schema and rejected. Em dash characters in text are rejected. Extreme strings above the limit are rejected.

Dates use exact `YYYY-MM-DD`. Created cannot be after the reporting date. Due may be null or a future date, but cannot precede created. Future deadlines are valid and not overdue. All envelopes must share `as_of` unless `--as-of` explicitly overrides it. No wall-clock date affects computation. Empty directories use the documented reference date 2026-09-30 and zero counts. No random seed is needed: fixture generation uses a fixed block design with no randomness.

Only JSON input is supported. CSV, YAML and other formats are rejected by name, not silently skipped. Subdirectories, `LABEL.md`, and `expectations.json` are ignored. Keep reports and state outside input directories.

## Rules and figures

Open and deferred questions are unanswered. A question is blocking only when both unanswered and declared blocking. Overdue means unanswered with due strictly before `as_of`; due today is not overdue. Decision names group by exact string. Counts reconcile: total = open + answered + deferred; unanswered = open + deferred. Every finding lists record IDs, and JSON reports include the full validated records and decision groupings.

## Subcommands

- `kur fixtures --out demo`: generate 200 synthetic records, hand-computed expectations and a labelling note. Use a dedicated fixture directory; existing fixture filenames are replaced.
- `kur run --input demo --as-of 2026-09-30`: validate every input and compute the register, atomically replacing `.kur/results.json` only after success.
- `kur report --format md`: show a report with provenance; `kur report --format json --out reports/register.json` atomically writes it.
- `kur questions --blocking --decision "Decision 01"`: show unanswered questions, optionally filtered by blocking or exact decision name.
- `kur decisions`: show affected decisions and their unanswered/blocking IDs.

Each command has `--help` and an example. Global `--state` must precede the command: `kur --state trial/results.json run --input trial/input`. Filters read the latest successful run. Failed runs leave the previous state untouched; rerun successfully before reporting changed inputs. Cached records are revalidated and their figures recomputed when read.

## Architecture

```text
JSON inputs -> cli.load_inputs -> core.validate_record -> core.aggregate
                                                   -> atomic local state
local state -> revalidation/aggregation -> report.render -> stdout or atomic file
fixtures.generate -> synthetic JSON + independent expectations + LABEL.md
```

Core logic has no I/O. CLI owns parsing, validation context and file operations. Rendering is deterministic. Equivalent inputs with the same filenames and reference date produce byte-identical reports. Absolute input locations and runtime timings are not embedded in reports.

## Honesty boundary and fixture policy

All counts are computed from explicit records; no time saved or money saved is reported because no measured baseline exists. Hypothetical or illustrative examples are labelled. Synthetic JSON includes `synthetic: true` and a conspicuous label because JSON cannot contain header comments. Every fixture folder also has `LABEL.md` with a synthetic header comment. Expectations have their own synthetic label. Every report and domain command has a provenance banner. No real trial results are shipped.

The planted design: Q001-Q100 open, Q101-Q160 answered, Q161-Q200 deferred. Q001-Q040 and Q181-Q200 block. Q001-Q060 and Q161-Q180 are overdue. Groups of 20 share a decision. Hand calculation: 200 total, 140 unanswered, 60 blockers, 80 overdue, 7 affected decisions. Tests compare complete ID sets as well as counts, and change a planted record to prove outputs are computed.

## Failure modes

Malformed JSON: `ParseError` with filename and parser line. Schema drift: `SchemaError` naming the file and offending field; schema line 1 denotes the envelope, not a parser location. Duplicate IDs abort the entire run. Missing directories/state: `MissingInput` with a usage hint. Unsupported formats: named schema errors. Invalid cached state: `StateError` with a rerun hint. File access or write failure: `FileError`, exit 2. Report/state writes use a temporary sibling and atomic replacement, cleaning temporary files on failure so an existing report survives. There is no concurrent-writer locking, and fixture generation is not a multi-file transaction.

## Two-week improvement hook and verdict

Start the evidence window on the first real use, not this synthetic build date. Keep private trial data outside this repository. For 14 days record daily usage and hand-check a sample of record classifications (unanswered, blocking, overdue and affected decision). Metric: classification error rate = incorrect checked classifications / total checked classifications. Record the denominator and reporting date; zero checked cases means unmeasured, not 0 percent error. Optional timing comparisons require a measured manual baseline on the same inputs.

If error exceeds 10 percent, fix the largest observed failure cause and repeat the sample, or kill with the reason. If unused, record that finding and kill. After the window record one explicit verdict and evidence in `VERDICT.md`: expand for daily use or revenue; integrate for substantial overlap; commercialise if a buyer would pay as-is; maintain as portfolio evidence otherwise; kill for no use or unmet acceptance criteria. No adoption, buyer interest or savings is inferred from fixture success.
