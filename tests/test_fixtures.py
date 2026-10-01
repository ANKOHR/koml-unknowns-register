import json
from koml_unknowns_register.fixtures import expectations
from koml_unknowns_register.cli import load_inputs

def test_fixtures_labelled_synthetic(fixture_dir):
    for p in fixture_dir.glob("*.json"):
        obj = json.loads(p.read_text())
        assert obj["synthetic"] and "SYNTHETIC" in obj["label"]
        assert all(r["synthetic"] for r in obj.get("records", []))
    assert "<!-- SYNTHETIC -->" in (fixture_dir / "LABEL.md").read_text()

def test_fixture_ground_truth_matches_hand_computed(fixture_dir):
    result = load_inputs(fixture_dir)
    assert result["metrics"] == dict(total=200, open=100, answered=60, deferred=40, unanswered=140, blocking_unanswered=60, overdue_unanswered=80, decisions_affected=7)
    for key in ("metrics", "unanswered_ids", "blocking_ids", "overdue_ids"):
        assert result[key] == expectations()[key]

def test_corrupted_ground_truth_changes_computation(fixture_dir):
    p = fixture_dir / "unknowns.json"
    obj = json.loads(p.read_text())
    obj["records"][0].update(status="answered", answer="Observed evidence")
    p.write_text(json.dumps(obj))
    result = load_inputs(fixture_dir)
    assert result["metrics"]["unanswered"] == 139
    assert "Q001" not in result["blocking_ids"]
