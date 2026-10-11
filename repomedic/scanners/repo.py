from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable
from repomedic.core.models import Finding, ScanContext, Severity
from repomedic.scanners.base import BaseScanner

# Sensitive filename patterns
SENSITIVE_EXACT_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    ".env.staging",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
}

SENSITIVE_SUFFIXES = (
    ".pem",
    ".key",
    ".pfx",
    ".p12",
    ".pkcs12",
    "credentials.json",
    "service-account.json",
    "auth.json",
)

EXAMPLE_SUFFIXES = (
    ".example",
    ".sample",
    ".template",
    ".dist",
    ".default",
    ".mock",
)

IGNORED_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
}

TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".sh",
    ".bash",
    ".env",
}

SECRET_PATTERNS = [
    (
        "Private Key Header",
        re.compile(r"-----BEGIN (?:RSA|DSA|EC|OPENSSH|PGP|PRIVATE) KEY-----"),
    ),
    (
        "AWS Access Key ID",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    ),
    (
        "GitHub Token",
        re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}\b"),
    ),
    (
        "Slack Token",
        re.compile(r"\bxox[baprs]-[0-9A-Za-z]{10,48}\b"),
    ),
]

# Exclusions to prevent false positives on documentation / placeholders
PLACEHOLDER_REGEX = re.compile(
    r"(?i)(example|placeholder|dummy|changeme|fake|mock|your_key|test_token)"
)


class RepoScanner(BaseScanner):
    name = "repo"
    description = "Repository hygiene and sensitive file/secret checks"

    def scan(self, context: ScanContext) -> list[Finding]:
        findings: list[Finding] = []
        root = context.repo_path

        findings.extend(self._check_hygiene(root))
        findings.extend(self._check_sensitive_files(root, context))
        findings.extend(self._check_hardcoded_secrets(root, context))

        return findings

    def _check_hygiene(self, root: Path) -> list[Finding]:
        findings: list[Finding] = []

        if not (root / ".gitignore").exists():
            findings.append(
                Finding(
                    code="RM001",
                    message="Missing .gitignore file",
                    severity=Severity.WARNING,
                    file_path=".gitignore",
                    suggestion="Add a .gitignore file tailored to your languages and frameworks.",
                )
            )

        readme_files = ["README.md", "README.rst", "README.txt", "README"]
        if not any((root / f).exists() for f in readme_files):
            findings.append(
                Finding(
                    code="RM002",
                    message="Missing README file",
                    severity=Severity.INFO,
                    file_path="README.md",
                    suggestion="Add a README.md file documenting project overview, setup, and usage.",
                )
            )

        license_files = ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"]
        if not any((root / f).exists() for f in license_files):
            findings.append(
                Finding(
                    code="RM003",
                    message="Missing LICENSE file",
                    severity=Severity.INFO,
                    file_path="LICENSE",
                    suggestion="Add an open-source license file (e.g. MIT, Apache-2.0, BSD-3-Clause).",
                )
            )

        return findings

    def _is_example_file(self, rel_path: str) -> bool:
        lower = rel_path.lower()
        if any(lower.endswith(sfx) for sfx in EXAMPLE_SUFFIXES):
            return True
        if ".env.example" in lower or ".env.sample" in lower:
            return True
        return False

    def _is_sensitive_file(self, rel_path: str) -> bool:
        if self._is_example_file(rel_path):
            return False
        filename = Path(rel_path).name.lower()
        if filename in SENSITIVE_EXACT_NAMES:
            return True
        if any(filename.endswith(sfx) for sfx in SENSITIVE_SUFFIXES):
            return True
        return False

    def _iterate_files(self, root: Path, context: ScanContext) -> Iterable[Path]:
        if context.is_git_repo and context.tracked_files:
            for rel in context.tracked_files:
                p = root / rel
                if p.is_file():
                    yield p
            return

        for p in root.rglob("*"):
            if not p.is_file():
                continue
            parts = p.relative_to(root).parts
            if any(part in IGNORED_DIRS for part in parts):
                continue
            yield p

    def _check_sensitive_files(self, root: Path, context: ScanContext) -> list[Finding]:
        findings: list[Finding] = []

        if context.is_git_repo:
            candidates = list(context.tracked_files)
        else:
            candidates = [
                str(p.relative_to(root)).replace("\\", "/")
                for p in self._iterate_files(root, context)
            ]

        for rel in candidates:
            if self._is_sensitive_file(rel):
                # When tracked in git, this is CRITICAL/ERROR
                severity = Severity.ERROR if context.is_git_repo else Severity.WARNING
                findings.append(
                    Finding(
                        code="RM004",
                        message=f"Potentially exposed sensitive file: {rel}",
                        severity=severity,
                        file_path=rel,
                        suggestion=f"Remove '{rel}' from version control and add it to .gitignore.",
                    )
                )

        return findings

    def _check_hardcoded_secrets(self, root: Path, context: ScanContext) -> list[Finding]:
        findings: list[Finding] = []

        for file_path in self._iterate_files(root, context):
            rel_path = str(file_path.relative_to(root)).replace("\\", "/")
            if self._is_example_file(rel_path):
                continue

            # Skip markdown, tests, minified or non-text
            name_lower = file_path.name.lower()
            if (
                file_path.suffix.lower() not in TEXT_EXTENSIONS
                or name_lower.startswith("test_")
                or name_lower.endswith("_test.py")
                or ".spec." in name_lower
                or ".test." in name_lower
                or ".min." in name_lower
            ):
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            # Limit scanning huge files (> 1MB)
            if len(content) > 1_000_000:
                continue

            for line_no, line in enumerate(content.splitlines(), start=1):
                if PLACEHOLDER_REGEX.search(line):
                    # Skip common examples/placeholders
                    continue

                for secret_type, regex in SECRET_PATTERNS:
                    if regex.search(line):
                        findings.append(
                            Finding(
                                code="RM005",
                                message=f"Potential hardcoded secret detected ({secret_type})",
                                severity=Severity.ERROR,
                                file_path=rel_path,
                                line=line_no,
                                suggestion="Revoke this secret, remove it from code, and load via environment variables.",
                            )
                        )
                        break  # one finding per line is enough

        return findings
