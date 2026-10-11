from pathlib import Path
import pytest
from repomedic.core.models import ScanContext, Severity
from repomedic.scanners.repo import RepoScanner

def test_repo_scanner_flags_missing_hygiene_files(tmp_path: Path):
    # Empty directory
    ctx = ScanContext(repo_path=tmp_path)
    scanner = RepoScanner()
    findings = scanner.scan(ctx)
    
    codes = {f.code for f in findings}
    assert "RM001" in codes  # missing .gitignore
    assert "RM002" in codes  # missing README
    assert "RM003" in codes  # missing LICENSE

def test_repo_scanner_passes_when_hygiene_files_exist(tmp_path: Path):
    (tmp_path / ".gitignore").write_text("*.pyc\n")
    (tmp_path / "README.md").write_text("# Test Repo\n")
    (tmp_path / "LICENSE").write_text("MIT License\n")
    
    ctx = ScanContext(repo_path=tmp_path)
    scanner = RepoScanner()
    findings = scanner.scan(ctx)
    
    codes = {f.code for f in findings}
    assert "RM001" not in codes
    assert "RM002" not in codes
    assert "RM003" not in codes

def test_repo_scanner_distinguishes_example_and_tracked_secrets(tmp_path: Path):
    # Example files should NOT be flagged
    (tmp_path / ".env.example").write_text("DB_PASS=changeme\n")
    (tmp_path / ".env.sample").write_text("API_KEY=sample\n")
    (tmp_path / "config.template.json").write_text("{}")
    
    # Real .env file that is git-tracked
    (tmp_path / ".env").write_text("SECRET=actual_password\n")
    
    ctx = ScanContext(
        repo_path=tmp_path,
        is_git_repo=True,
        tracked_files={".env.example", ".env.sample", "config.template.json", ".env"}
    )
    scanner = RepoScanner()
    findings = scanner.scan(ctx)
    
    env_findings = [f for f in findings if f.code == "RM004"]
    assert len(env_findings) == 1
    assert env_findings[0].file_path == ".env"
    assert env_findings[0].severity == Severity.ERROR

def test_repo_scanner_ignores_untracked_env_in_git_repo(tmp_path: Path):
    # If .env exists locally (e.g. developer's local machine) but is NOT tracked by Git:
    (tmp_path / ".env").write_text("LOCAL_SECRET=12345\n")
    ctx = ScanContext(
        repo_path=tmp_path,
        is_git_repo=True,
        tracked_files={"README.md"}
    )
    (tmp_path / "README.md").write_text("# Hello\n")
    (tmp_path / ".gitignore").write_text(".env\n")
    
    scanner = RepoScanner()
    findings = scanner.scan(ctx)
    
    # RM004 should NOT be flagged because .env is untracked in git
    assert not any(f.code == "RM004" for f in findings)

def test_repo_scanner_detects_committed_private_key(tmp_path: Path):
    key_file = tmp_path / "id_rsa"
    key_file.write_text("-----BEGIN OPENSSH PRIVATE KEY-----\ntest\n")
    
    ctx = ScanContext(
        repo_path=tmp_path,
        is_git_repo=True,
        tracked_files={"id_rsa"}
    )
    scanner = RepoScanner()
    findings = scanner.scan(ctx)
    
    assert any(f.code == "RM004" and "id_rsa" in str(f.file_path) for f in findings)

def test_repo_scanner_detects_hardcoded_secrets(tmp_path: Path):
    app_file = tmp_path / "app.py"
    app_file.write_text('AWS_KEY = "AKIA1234567890ABCDEF"\n')
    
    ctx = ScanContext(
        repo_path=tmp_path,
        is_git_repo=True,
        tracked_files={"app.py"}
    )
    scanner = RepoScanner()
    findings = scanner.scan(ctx)
    
    secret_findings = [f for f in findings if f.code == "RM005"]
    assert len(secret_findings) >= 1
    assert secret_findings[0].file_path == "app.py"
    assert secret_findings[0].severity == Severity.ERROR

def test_repo_scanner_ignores_secret_placeholders(tmp_path: Path):
    app_file = tmp_path / "app.py"
    app_file.write_text('AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\nAPI_KEY = "YOUR_KEY_HERE"\n')
    
    ctx = ScanContext(
        repo_path=tmp_path,
        is_git_repo=True,
        tracked_files={"app.py"}
    )
    scanner = RepoScanner()
    findings = scanner.scan(ctx)
    
    assert not any(f.code == "RM005" for f in findings)

