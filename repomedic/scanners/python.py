from __future__ import annotations

import re
from pathlib import Path
from repomedic.core.models import Finding, ScanContext, Severity
from repomedic.core.toml_compat import loads
from repomedic.scanners.base import BaseScanner

APP_INDICATOR_FILES = {
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Procfile",
    "serverless.yml",
    "wsgi.py",
    "asgi.py",
    "manage.py",
    "app.py",
}

APP_FRAMEWORKS = {
    "fastapi",
    "django",
    "flask",
    "tornado",
    "starlette",
    "sanic",
    "celery",
    "streamlit",
    "dash",
}

LOCKFILES = {
    "poetry.lock",
    "Pipfile.lock",
    "uv.lock",
    "pdm.lock",
    "requirements.lock",
    "requirements-lock.txt",
    "conda-lock.yml",
}

VERSION_SPEC_PATTERN = re.compile(r"([=><~^!])")


class PythonScanner(BaseScanner):
    name = "python"
    description = "Python project configuration, dependencies, and lockfile diagnostics"

    def scan(self, context: ScanContext) -> list[Finding]:
        root = context.repo_path
        if not self._is_python_repo(root):
            return []

        findings: list[Finding] = []
        is_app = self._detect_if_application(root)

        findings.extend(self._check_lockfiles(root, is_app))
        findings.extend(self._check_requirements_files(root, is_app))
        findings.extend(self._check_pyproject_toml(root))

        return findings

    def _is_python_repo(self, root: Path) -> bool:
        indicators = [
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "Pipfile",
            "requirements.txt",
        ]
        if any((root / f).exists() for f in indicators):
            return True
        if (root / "requirements").is_dir() and any((root / "requirements").glob("*.txt")):
            return True
        # Check if any .py files exist (shallow search)
        return any(root.glob("*.py")) or any(root.glob("*/*.py"))

    def _detect_if_application(self, root: Path) -> bool:
        # Check indicator files
        for f in APP_INDICATOR_FILES:
            if (root / f).exists():
                return True

        # Check framework dependencies in requirements or pyproject
        req_file = root / "requirements.txt"
        if req_file.exists():
            try:
                content = req_file.read_text(encoding="utf-8", errors="ignore").lower()
                for fw in APP_FRAMEWORKS:
                    if re.search(rf"\b{fw}\b", content):
                        return True
            except OSError:
                pass

        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            try:
                content = pyproject.read_text(encoding="utf-8", errors="ignore").lower()
                for fw in APP_FRAMEWORKS:
                    if re.search(rf"\b{fw}\b", content):
                        return True
            except OSError:
                pass

        return False

    def _check_lockfiles(self, root: Path, is_app: bool) -> list[Finding]:
        findings: list[Finding] = []
        has_lockfile = any((root / lf).exists() for lf in LOCKFILES)

        if not has_lockfile and is_app:
            findings.append(
                Finding(
                    code="RM101",
                    message="Python application missing dependency lockfile (e.g. uv.lock, poetry.lock, Pipfile.lock)",
                    severity=Severity.WARNING,
                    file_path=None,
                    suggestion="Generate and commit a lockfile using uv, poetry, pipenv, or pip-compile to ensure reproducible deployments.",
                )
            )

        return findings

    def _check_requirements_files(self, root: Path, is_app: bool) -> list[Finding]:
        findings: list[Finding] = []
        req_paths = set(root.glob("requirements*.txt")) | set(root.glob("requirements/*.txt"))

        for req_path in sorted(req_paths):
            rel_path = str(req_path.relative_to(root)).replace("\\", "/")
            try:
                lines = req_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError:
                continue

            for line_no, raw_line in enumerate(lines, start=1):
                # Strip inline comments
                line = raw_line.split("#", 1)[0].strip()
                if not line:
                    continue

                # Insecure HTTP check
                if "http://" in line:
                    sanitized = re.sub(r"://([^:@]+):([^@]+)@", "://***:***@", line)
                    findings.append(
                        Finding(
                            code="RM105",
                            message=f"Insecure plain HTTP package index or URL: {sanitized}",
                            severity=Severity.ERROR,
                            file_path=rel_path,
                            line=line_no,
                            suggestion="Use secure HTTPS URLs for package indices and remote dependencies.",
                        )
                    )
                    continue

                # Flags / options like -r or -i or --extra-index-url
                if line.startswith("-"):
                    continue

                # Unpinned package check
                pkg_token = line.split(";")[0].strip()  # strip environment markers
                if not VERSION_SPEC_PATTERN.search(pkg_token):
                    # Clean package name from extras e.g. requests[security]
                    pkg_name = pkg_token.split("[")[0].strip()
                    if pkg_name and re.match(r"^[A-Za-z0-9_\-\.]+$", pkg_name):
                        findings.append(
                            Finding(
                                code="RM102",
                                message=f"Unpinned dependency '{pkg_name}' found in {rel_path}",
                                severity=Severity.WARNING if is_app else Severity.INFO,
                                file_path=rel_path,
                                line=line_no,
                                suggestion=f"Specify a version constraint for '{pkg_name}' (e.g. {pkg_name}==... or {pkg_name}>=...).",
                            )
                        )

        return findings

    def _check_pyproject_toml(self, root: Path) -> list[Finding]:
        findings: list[Finding] = []
        pyproject_file = root / "pyproject.toml"
        if not pyproject_file.exists():
            return findings

        rel_path = "pyproject.toml"
        try:
            content = pyproject_file.read_text(encoding="utf-8")
            data = loads(content)
        except Exception as err:
            findings.append(
                Finding(
                    code="RM100",
                    message=f"Unable to parse pyproject.toml: {err}",
                    severity=Severity.ERROR,
                    file_path=rel_path,
                    suggestion="Check pyproject.toml syntax and structure.",
                )
            )
            return findings

        project_table = data.get("project")
        if isinstance(project_table, dict):
            if "requires-python" not in project_table:
                findings.append(
                    Finding(
                        code="RM104",
                        message="Missing 'project.requires-python' in pyproject.toml",
                        severity=Severity.INFO,
                        file_path=rel_path,
                        suggestion="Specify supported Python versions in pyproject.toml (e.g. requires-python = '>=3.10').",
                    )
                )

            if "build-system" not in data:
                findings.append(
                    Finding(
                        code="RM103",
                        message="pyproject.toml defines [project] but is missing [build-system]",
                        severity=Severity.WARNING,
                        file_path=rel_path,
                        suggestion="Add [build-system] with 'requires' and 'build-backend' (e.g. setuptools or flit_core).",
                    )
                )

        return findings
