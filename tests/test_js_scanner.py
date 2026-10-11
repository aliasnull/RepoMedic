import json
from pathlib import Path
import pytest
from repomedic.core.models import ScanContext, Severity
from repomedic.scanners.js import JsScanner

def test_js_scanner_ignores_non_js_repo(tmp_path: Path):
    (tmp_path / "main.py").write_text("print('hi')\n")
    ctx = ScanContext(repo_path=tmp_path)
    scanner = JsScanner()
    findings = scanner.scan(ctx)
    assert len(findings) == 0

def test_js_scanner_flags_malformed_package_json(tmp_path: Path):
    (tmp_path / "package.json").write_text("{ invalid json")
    ctx = ScanContext(repo_path=tmp_path)
    scanner = JsScanner()
    findings = scanner.scan(ctx)
    assert any(f.code == "RM200" for f in findings)

def test_js_scanner_context_aware_missing_lockfile_for_app(tmp_path: Path):
    pkg_data = {
        "name": "my-app",
        "private": True,
        "dependencies": {
            "express": "^4.18.2"
        }
    }
    (tmp_path / "package.json").write_text(json.dumps(pkg_data))
    
    ctx = ScanContext(repo_path=tmp_path)
    scanner = JsScanner()
    findings = scanner.scan(ctx)
    
    lock_findings = [f for f in findings if f.code == "RM201"]
    assert len(lock_findings) == 1
    assert lock_findings[0].severity == Severity.WARNING

def test_js_scanner_context_aware_lockfile_for_public_library(tmp_path: Path):
    pkg_data = {
        "name": "my-library",
        "version": "1.0.0",
        "main": "index.js",
        "dependencies": {
            "lodash": "^4.17.21"
        }
    }
    (tmp_path / "package.json").write_text(json.dumps(pkg_data))
    (tmp_path / "index.js").write_text("module.exports = {};")
    
    ctx = ScanContext(repo_path=tmp_path)
    scanner = JsScanner()
    findings = scanner.scan(ctx)
    
    # Should not produce a WARNING or ERROR for lockfile on public library
    assert not any(f.code == "RM201" and f.severity >= Severity.WARNING for f in findings)

def test_js_scanner_flags_conflicting_multiple_lockfiles(tmp_path: Path):
    (tmp_path / "package.json").write_text('{"name": "test"}')
    (tmp_path / "package-lock.json").write_text('{}')
    (tmp_path / "yarn.lock").write_text('# yarn lock')
    
    ctx = ScanContext(repo_path=tmp_path)
    scanner = JsScanner()
    findings = scanner.scan(ctx)
    
    conflict = [f for f in findings if f.code == "RM202"]
    assert len(conflict) == 1
    assert conflict[0].severity == Severity.WARNING

def test_js_scanner_flags_missing_tsconfig_when_ts_files_exist(tmp_path: Path):
    (tmp_path / "package.json").write_text('{"name": "ts-project"}')
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "index.ts").write_text("export const x: number = 42;")
    
    ctx = ScanContext(repo_path=tmp_path)
    scanner = JsScanner()
    findings = scanner.scan(ctx)
    
    ts_findings = [f for f in findings if f.code == "RM203"]
    assert len(ts_findings) == 1
    assert ts_findings[0].severity == Severity.WARNING

def test_js_scanner_flags_wildcard_and_insecure_dependencies(tmp_path: Path):
    pkg_data = {
        "name": "test-pkg",
        "dependencies": {
            "bad-dep": "*",
            "insecure-dep": "http://example.com/tarball.tgz",
            "latest-dep": "latest"
        }
    }
    (tmp_path / "package.json").write_text(json.dumps(pkg_data))
    
    ctx = ScanContext(repo_path=tmp_path)
    scanner = JsScanner()
    findings = scanner.scan(ctx)
    
    codes = {f.code for f in findings}
    assert "RM204" in codes  # insecure http URL
    assert "RM205" in codes  # wildcard/latest

def test_js_scanner_redacts_credentials_in_insecure_dependency(tmp_path: Path):
    pkg_data = {
        "name": "test-pkg",
        "dependencies": {
            "private-dep": "http://token:secret12345@npm.corp.internal/tarball.tgz"
        }
    }
    (tmp_path / "package.json").write_text(json.dumps(pkg_data))
    
    ctx = ScanContext(repo_path=tmp_path)
    scanner = JsScanner()
    findings = scanner.scan(ctx)
    
    insecure = [f for f in findings if f.code == "RM204"]
    assert len(insecure) == 1
    assert "secret12345" not in insecure[0].message
    assert "token:***:***@" in insecure[0].message or "***:***@" in insecure[0].message

def test_js_scanner_detects_tsx_and_modern_extensions(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "App.tsx").write_text("export const App = () => <div>Hello</div>;")
    
    ctx = ScanContext(repo_path=tmp_path)
    scanner = JsScanner()
    findings = scanner.scan(ctx)
    
    # Missing tsconfig should be flagged on TSX files
    assert any(f.code == "RM203" for f in findings)

