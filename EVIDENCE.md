# Local synthetic acceptance evidence

Measured on 2026-10-01, Windows, Python 3.12.10, CPU only.

- Pytest: 31 passed (0.42 seconds in final recorded suite run).
- Installed kur executable: fixtures -> run -> Markdown report, three fresh processes: 0.641734 seconds measured wall time.
- Report process alone: 0.192038 seconds measured wall time.
- All commands exited 0 with no tracebacks.
- Fixture: 200 synthetic records; 100 open, 60 answered, 40 deferred; 140 unanswered, 60 blocking unanswered, 80 overdue unanswered, 7 decisions affected.
- Full ID sets match independent planted expectations, zero false positives. Mutation of Q001 to answered reduces unanswered count to 139 and removes its blocking finding.
- Reports include the synthetic provenance banner. Empty inputs, malformed files, schema drift, write failure, Unicode, long text and deterministic repeated output are covered by tests.

These timings measure this local run only. They are not a performance guarantee or a measurement of time saved. Real-world accuracy, adoption, savings and commercial value remain unmeasured. No real trial results are shipped.
