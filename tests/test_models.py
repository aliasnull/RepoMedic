from pathlib import Path
import pytest
from repomedic.core.models import Finding, Severity, DiagnosticResult, ScanContext
from repomedic.scanners.base import BaseScanner

def test_severity_ordering_and_values():
    assert Severity.INFO.value == "INFO"
    assert Severity.WARNING.value == "WARNING"
    assert Severity.ERROR.value == "ERROR"
    assert Severity.INFO < Severity.WARNING < Severity.ERROR

def test_finding_creation_and_to_dict():
    finding = Finding(
        code="RM001",
        message="Missing .gitignore file",
        severity=Severity.WARNING,
        file_path=".gitignore",
        line=None,
        suggestion="Create a .gitignore file tailored to your stack."
    )
    assert finding.code == "RM001"
    d = finding.to_dict()
    assert d["code"] == "RM001"
    assert d["severity"] == "WARNING"
    assert d["file_path"] == ".gitignore"
    assert d["line"] is None
    assert "suggestion" in d

def test_diagnostic_result_properties():
    f1 = Finding(code="RM001", message="Warning 1", severity=Severity.WARNING)
    f2 = Finding(code="RM002", message="Error 1", severity=Severity.ERROR)
    f3 = Finding(code="RM003", message="Info 1", severity=Severity.INFO)
    
    result = DiagnosticResult(findings=[f1, f2, f3], scanned_files_count=10)
    assert result.has_errors is True
    assert result.has_warnings is True
    assert result.counts_by_severity() == {"ERROR": 1, "WARNING": 1, "INFO": 1}
    
    # filter by min severity
    errors_only = result.filter_by_min_severity(Severity.ERROR)
    assert len(errors_only) == 1
    assert errors_only[0].code == "RM002"
    
    warns_and_errors = result.filter_by_min_severity(Severity.WARNING)
    assert len(warns_and_errors) == 2

def test_scan_context_git_tracking(tmp_path: Path):
    ctx = ScanContext(
        repo_path=tmp_path,
        is_git_repo=True,
        tracked_files={"src/main.py", "README.md", ".env", ".gitignore", ".github/workflows/ci.yml"}
    )
    assert ctx.is_tracked("src/main.py") is True
    assert ctx.is_tracked("./src/main.py") is True
    assert ctx.is_tracked(".env") is True
    assert ctx.is_tracked("./.env") is True
    assert ctx.is_tracked(".gitignore") is True
    assert ctx.is_tracked("secret.env") is False

def test_base_scanner_subclass():
    class DummyScanner(BaseScanner):
        name = "dummy"
        description = "Dummy scanner for tests"
        def scan(self, context: ScanContext) -> list[Finding]:
            return [Finding(code="RM999", message="Dummy", severity=Severity.INFO)]

    scanner = DummyScanner()
    findings = scanner.scan(ScanContext(repo_path=Path(".")))
    assert len(findings) == 1
    assert findings[0].code == "RM999"
