import json
from pathlib import Path
from repomedic.core.models import Finding, Severity, DiagnosticResult
from repomedic.reporters.console import ConsoleReporter
from repomedic.reporters.json_rep import JsonReporter
from repomedic.reporters.github import GitHubReporter

def test_console_reporter_formatting():
    f1 = Finding(
        code="RM001",
        message="Missing .gitignore file",
        severity=Severity.WARNING,
        file_path=".gitignore",
        suggestion="Add a .gitignore file."
    )
    result = DiagnosticResult(findings=[f1], scanned_files_count=5, duration_ms=12.5)
    reporter = ConsoleReporter(use_color=False)
    output = reporter.format(result)
    
    assert "[WARNING] RM001" in output
    assert "Missing .gitignore file" in output
    assert "Fix: Add a .gitignore file." in output
    assert "Warnings: 1" in output

def test_json_reporter_formatting():
    f1 = Finding(
        code="RM004",
        message="Potentially exposed sensitive file: .env",
        severity=Severity.ERROR,
        file_path=".env",
        suggestion="Remove from git"
    )
    result = DiagnosticResult(findings=[f1], scanned_files_count=1)
    reporter = JsonReporter()
    output = reporter.format(result)
    
    parsed = json.loads(output)
    assert parsed["counts"]["ERROR"] == 1
    assert parsed["findings"][0]["code"] == "RM004"
    assert parsed["has_errors"] is True

def test_github_reporter_workflow_commands(tmp_path: Path, monkeypatch):
    summary_file = tmp_path / "step_summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))
    
    f1 = Finding(
        code="RM005",
        message="Hardcoded secret detected",
        severity=Severity.ERROR,
        file_path="app.py",
        line=15,
        suggestion="Use env vars"
    )
    f2 = Finding(
        code="RM001",
        message="Missing .gitignore",
        severity=Severity.WARNING,
        file_path=".gitignore"
    )
    result = DiagnosticResult(findings=[f1, f2], scanned_files_count=2)
    reporter = GitHubReporter()
    output = reporter.format(result)
    
    assert "::error file=app.py,line=15,title=RM005::Hardcoded secret detected" in output
    assert "::warning file=.gitignore,title=RM001::Missing .gitignore" in output
    
    # Check that GITHUB_STEP_SUMMARY was written
    assert summary_file.exists()
    summary_content = summary_file.read_text()
    assert "### RepoMedic Diagnostic Summary" in summary_content
    assert "| Error | 1 |" in summary_content
