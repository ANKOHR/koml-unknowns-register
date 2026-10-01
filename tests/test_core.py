from datetime import date
import pytest
from koml_unknowns_register.core import aggregate, SchemaError
from koml_unknowns_register.fixtures import fixture_records

@pytest.mark.parametrize("field,value", [("amount", -1), ("created", "2027-01-01"), ("question", "x" * 100001), ("blocking", 1), ("status", []), ("due", "2026-08-01"), ("answer", "invented"), ("question", "bad" + chr(0x2014))], ids=["negative-amount", "future-created", "extreme-string", "invalid-bool", "invalid-status", "early-due", "unexpected-answer", "forbidden-punctuation"])
def test_rejects_adversarial_values(field, value):
    r = fixture_records()[0]
    r[field] = value
    with pytest.raises(SchemaError, match=field):
        aggregate([r], date(2026,9,30), [])

def test_duplicate_ids():
    r = fixture_records()[0]
    with pytest.raises(SchemaError, match="duplicate"):
        aggregate([r,r], date(2026,9,30), [])

def test_handles_unicode_and_long_inputs():
    r = fixture_records()[0]
    r["question"] = chr(0x95ee) * 50000
    r["decision"] = r"C:\Users\Henry\decisions"
    assert aggregate([r], date(2026,9,30), [])["records"] == [r]

def test_due_boundary():
    r = fixture_records()[0]
    for due in (None, "2026-09-30", "2027-01-01"):
        r["due"] = due
        assert aggregate([r], date(2026,9,30), [])["overdue_ids"] == []
