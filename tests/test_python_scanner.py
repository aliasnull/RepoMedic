from pathlib import Path
import pytest
from repomedic.core.models import ScanContext, Severity
from repomedic.scanners.python import PythonScanner

def test_python_scanner_ignores_non_python_repo(tmp_path: Path):
    (tmp_path / "index.js").write_text("console.log('hi');")
    ctx = ScanContext(repo_path=tmp_path)
    scanner = PythonScanner()
    findings = scanner.scan(ctx)
    assert len(findings) == 0

def test_python_scanner_detects_unpinned_requirements_in_app(tmp_path: Path):
    # App has Dockerfile and requirements.txt with unpinned dep
    (tmp_path / "Dockerfile").write_text("FROM python:3.11\n")
    (tmp_path / "requirements.txt").write_text("fastapi\nuvicorn==0.23.2\n")
    
    ctx = ScanContext(repo_path=tmp_path)
    scanner = PythonScanner()
    findings = scanner.scan(ctx)
    
    unpinned = [f for f in findings if f.code == "RM102"]
    assert len(unpinned) == 1
    assert "fastapi" in unpinned[0].message
    assert unpinned[0].severity == Severity.WARNING

def test_python_scanner_flags_insecure_http_index(tmp_path: Path):
    (tmp_path / "requirements.txt").write_text("--index-url http://insecure-repo.internal/simple\nflask==2.0.1\n")
    ctx = ScanContext(repo_path=tmp_path)
    scanner = PythonScanner()
    findings = scanner.scan(ctx)
    
    insecure = [f for f in findings if f.code == "RM105"]
    assert len(insecure) == 1
    assert insecure[0].severity == Severity.ERROR

def test_python_scanner_context_aware_lockfile_for_app(tmp_path: Path):
    # An application (Dockerfile present, dependencies present, but no lockfile)
    (tmp_path / "Dockerfile").write_text("FROM python:3.11\n")
    (tmp_path / "requirements.txt").write_text("flask==2.3.0\n")
    
    ctx = ScanContext(repo_path=tmp_path)
    scanner = PythonScanner()
    findings = scanner.scan(ctx)
    
    lock_findings = [f for f in findings if f.code == "RM101"]
    assert len(lock_findings) == 1
    assert lock_findings[0].severity == Severity.WARNING  # Not an ERROR!

def test_python_scanner_context_aware_lockfile_does_not_error_for_library(tmp_path: Path):
    # A library with pyproject.toml and src layout, no Dockerfile, no app markers
    (tmp_path / "pyproject.toml").write_text("""
    [build-system]
    requires = ["setuptools>=61.0.0"]
    build-backend = "setuptools.build_meta"

    [project]
    name = "mylib"
    version = "0.1.0"
    requires-python = ">=3.10"
    dependencies = ["requests>=2.28.0"]
    """)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "mylib.py").write_text("def hello(): pass\n")
    
    ctx = ScanContext(repo_path=tmp_path)
    scanner = PythonScanner()
    findings = scanner.scan(ctx)
    
    # Should NOT have an ERROR or high-severity warning for missing lockfile on a library
    assert not any(f.code == "RM101" and f.severity == Severity.ERROR for f in findings)

def test_python_scanner_recommends_requires_python_when_missing(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text("""
    [project]
    name = "mylib"
    version = "0.1.0"
    """)
    ctx = ScanContext(repo_path=tmp_path)
    scanner = PythonScanner()
    findings = scanner.scan(ctx)
    
    py_ver_findings = [f for f in findings if f.code == "RM104"]
    assert len(py_ver_findings) == 1
    assert py_ver_findings[0].severity == Severity.INFO
