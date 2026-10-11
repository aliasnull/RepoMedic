from pathlib import Path
from repomedic.core.engine import ScanEngine
from repomedic.core.models import Finding, Severity, ScanContext
from repomedic.scanners.base import BaseScanner

class MockScanner(BaseScanner):
    name = "mock"
    description = "Mock test scanner"
    def scan(self, context: ScanContext) -> list[Finding]:
        return [
            Finding(code="RM999", message="Test Mock Issue", severity=Severity.WARNING, file_path="mock.txt")
        ]

def test_engine_run_with_custom_scanner(tmp_path: Path):
    engine = ScanEngine(scanners=[MockScanner()])
    result = engine.run(tmp_path)
    
    assert len(result.findings) == 1
    assert result.findings[0].code == "RM999"
    assert result.has_warnings is True
    assert result.duration_ms >= 0

def test_engine_git_integration(tmp_path: Path):
    # Test tracking detection in non-git vs git dir
    engine = ScanEngine()
    ctx = engine.build_context(tmp_path)
    assert ctx.repo_path == tmp_path
    assert isinstance(ctx.tracked_files, set)
