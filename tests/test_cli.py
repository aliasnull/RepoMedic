from pathlib import Path
import json
import pytest
from repomedic.cli import main

def test_cli_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "0.1.2" in captured.out

def test_cli_version_short_flag(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["-v"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "0.1.2" in captured.out

def test_cli_scan_shorthand_path(tmp_path: Path, capsys):
    (tmp_path / ".gitignore").write_text("*.pyc\n")
    (tmp_path / "README.md").write_text("# Test\n")
    (tmp_path / "LICENSE").write_text("MIT\n")
    
    # Invoking with just the path argument (implicit scan)
    exit_code = main([str(tmp_path), "--no-color"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "All repository diagnostics passed" in captured.out

def test_cli_scan_clean_dir(tmp_path: Path, capsys):
    # Setup clean repo
    (tmp_path / ".gitignore").write_text("*.pyc\n")
    (tmp_path / "README.md").write_text("# Test\n")
    (tmp_path / "LICENSE").write_text("MIT\n")
    
    exit_code = main(["scan", str(tmp_path), "--format", "console", "--no-color"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "All repository diagnostics passed" in captured.out

def test_cli_scan_json_output(tmp_path: Path, capsys):
    exit_code = main(["scan", str(tmp_path), "--format", "json", "--fail-on", "none"])
    assert exit_code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "findings" in data
    assert "counts" in data

def test_cli_fail_on_threshold(tmp_path: Path):
    # Missing .gitignore creates a WARNING
    (tmp_path / "README.md").write_text("# Test\n")
    (tmp_path / "LICENSE").write_text("MIT\n")
    
    # --fail-on error should succeed (exit 0) since there's only warning
    code_err = main(["scan", str(tmp_path), "--fail-on", "error"])
    assert code_err == 0
    
    # --fail-on warning should fail (exit 1)
    code_warn = main(["scan", str(tmp_path), "--fail-on", "warning"])
    assert code_warn == 1

def test_cli_invalid_path(capsys):
    code = main(["scan", "non_existent_directory_xyz123"])
    assert code == 2
    captured = capsys.readouterr()
    assert "Error: Path does not exist" in captured.err
