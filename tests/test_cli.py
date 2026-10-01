import json
import time
import pytest
from koml_unknowns_register.cli import main, load_inputs

def call(tmp_path, *args):
    return main(["--state", str(tmp_path / "results.json"), *args])

def test_run_completes_on_fixture(fixture_dir, tmp_path, capsys):
    start = time.perf_counter()
    call(tmp_path, "run", "--input", str(fixture_dir))
    call(tmp_path, "report", "--format", "md")
    assert time.perf_counter() - start < 5
    assert "Data provenance:" in capsys.readouterr().out

def test_cli_smoke_all_subcommands(tmp_path, capsys):
    for command in ("fixtures", "run", "report", "questions", "decisions"):
        with pytest.raises(SystemExit) as e:
            main([command, "--help"])
        assert e.value.code == 0
        assert "Example:" in capsys.readouterr().out
    call(tmp_path, "fixtures", "--out", str(tmp_path / "demo"))
    call(tmp_path, "run", "--input", str(tmp_path / "demo"))
    call(tmp_path, "questions", "--blocking", "--decision", "Decision 01")
    call(tmp_path, "decisions")
    call(tmp_path, "report", "--format", "json", "--out", str(tmp_path / "report.json"))
    assert json.loads((tmp_path / "report.json").read_text())["metrics"]["total"] == 200

def test_empty_input_renders_without_traceback(tmp_path, capsys):
    folder = tmp_path / "empty"
    folder.mkdir()
    call(tmp_path, "run", "--input", str(folder))
    call(tmp_path, "report")
    assert all(n == 0 for n in load_inputs(folder)["metrics"].values())
    assert "zero records" in capsys.readouterr().out

def test_malformed_input_named_error(tmp_path, capsys):
    (tmp_path / "bad.json").write_text('{\n bad')
    with pytest.raises(SystemExit):
        call(tmp_path, "run", "--input", str(tmp_path))
    assert "ParseError: bad.json: line 2" in capsys.readouterr().err

def test_missing_input_named_error(tmp_path, capsys):
    with pytest.raises(SystemExit):
        call(tmp_path, "run", "--input", str(tmp_path / "missing"))
    assert "MissingInput" in capsys.readouterr().err

def test_report_write_failure_no_partial_files(fixture_dir, tmp_path, capsys):
    call(tmp_path, "run", "--input", str(fixture_dir))
    dest = tmp_path / "directory"
    dest.mkdir()
    before = set(tmp_path.iterdir())
    with pytest.raises(SystemExit):
        call(tmp_path, "report", "--out", str(dest))
    assert set(tmp_path.iterdir()) == before
    assert "FileError" in capsys.readouterr().err

def test_real_and_mixed_provenance(fixture_dir):
    source = json.loads((fixture_dir / "unknowns.json").read_text())
    r = source["records"][0]
    r.update(id="Henry-1", synthetic=False)
    source.update(synthetic=False, label="REAL user-entered data", records=[r])
    (fixture_dir / "real.json").write_text(json.dumps(source))
    assert [s["synthetic"] for s in load_inputs(fixture_dir)["provenance"]] == [False, True]


def test_corrupt_state_named_error(tmp_path, capsys):
    (tmp_path / "results.json").write_text('{}')
    with pytest.raises(SystemExit):
        call(tmp_path, "report")
    assert "StateError" in capsys.readouterr().err

def test_schema_drift_named_field(fixture_dir, tmp_path, capsys):
    path = fixture_dir / "unknowns.json"
    obj = json.loads(path.read_text())
    obj["records"][0]["amount"] = -10
    path.write_text(json.dumps(obj))
    with pytest.raises(SystemExit):
        call(tmp_path, "run", "--input", str(fixture_dir))
    err = capsys.readouterr().err
    assert "unknowns.json: line 1" in err and "amount" in err

def test_unsupported_malformed_formats(tmp_path, capsys):
    (tmp_path / "bad.yaml").write_text('bad: [')
    with pytest.raises(SystemExit):
        call(tmp_path, "run", "--input", str(tmp_path))
    assert "bad.yaml: line 1: format" in capsys.readouterr().err

def test_cli_byte_identical(fixture_dir, tmp_path, capsys):
    snapshots = []
    for _ in range(2):
        call(tmp_path, "run", "--input", str(fixture_dir))
        call(tmp_path, "report", "--out", str(tmp_path / "output.md"))
        snapshots.append(((tmp_path / "results.json").read_bytes(), (tmp_path / "output.md").read_bytes()))
    assert snapshots[0] == snapshots[1]
    assert chr(0x2014) not in capsys.readouterr().out
