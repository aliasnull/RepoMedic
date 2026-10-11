from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Sequence
from repomedic.core.models import DiagnosticResult, Finding, ScanContext
from repomedic.scanners.base import BaseScanner
from repomedic.scanners.repo import RepoScanner
from repomedic.scanners.python import PythonScanner
from repomedic.scanners.js import JsScanner


class ScanEngine:
    def __init__(self, scanners: Sequence[BaseScanner] | None = None) -> None:
        if scanners is None:
            self.scanners: list[BaseScanner] = [
                RepoScanner(),
                PythonScanner(),
                JsScanner(),
            ]
        else:
            self.scanners = list(scanners)

    def build_context(self, repo_path: Path) -> ScanContext:
        resolved = repo_path.resolve()
        is_git = False
        tracked: set[str] = set()

        # Check git status
        try:
            res = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=resolved,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if res.returncode == 0 and res.stdout.strip() == "true":
                is_git = True
                files_res = subprocess.run(
                    ["git", "ls-files"],
                    cwd=resolved,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if files_res.returncode == 0:
                    tracked = {
                        line.strip().replace("\\", "/")
                        for line in files_res.stdout.splitlines()
                        if line.strip()
                    }
        except Exception:
            is_git = False
            tracked = set()

        return ScanContext(
            repo_path=resolved,
            is_git_repo=is_git,
            tracked_files=tracked,
        )

    def run(self, repo_path: Path) -> DiagnosticResult:
        context = self.build_context(repo_path)
        start_time = time.perf_counter()

        findings: list[Finding] = []
        for scanner in self.scanners:
            scanner_findings = scanner.scan(context)
            findings.extend(scanner_findings)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Estimate scanned files count
        if context.is_git_repo and context.tracked_files:
            file_count = len(context.tracked_files)
        else:
            file_count = sum(1 for p in repo_path.rglob("*") if p.is_file() and ".git" not in p.parts)

        return DiagnosticResult(
            findings=findings,
            duration_ms=round(duration_ms, 2),
            scanned_files_count=file_count,
        )
