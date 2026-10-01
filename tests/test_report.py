import json
from koml_unknowns_register.cli import load_inputs
from koml_unknowns_register.fixtures import expectations
from koml_unknowns_register.report import render

def test_report_matches_ground_truth_exact(fixture_dir):
    result = json.loads(render(load_inputs(fixture_dir), "json"))
    for key in ("metrics", "unanswered_ids", "blocking_ids", "overdue_ids"):
        assert result[key] == expectations()[key]

def test_report_zero_false_positives(fixture_dir):
    result = load_inputs(fixture_dir)
    for key in ("unanswered_ids", "blocking_ids", "overdue_ids"):
        assert set(result[key]) == set(expectations()[key])

def test_report_carries_provenance_banner(fixture_dir):
    for fmt in ("md", "json"):
        output = render(load_inputs(fixture_dir), fmt)
        assert "Data provenance:" in output and "SYNTHETIC fixture data" in output

def test_hypothetical_figures_labelled(fixture_dir):
    for fmt in ("md", "json"):
        assert "Time and money saved are unmeasured and are not reported" in render(load_inputs(fixture_dir), fmt)

def test_determinism_byte_identical(fixture_dir):
    for fmt in ("md", "json"):
        assert render(load_inputs(fixture_dir), fmt).encode() == render(load_inputs(fixture_dir), fmt).encode()

def test_no_em_dashes_in_outputs(fixture_dir):
    for fmt in ("md", "json"):
        assert chr(0x2014) not in render(load_inputs(fixture_dir), fmt)
