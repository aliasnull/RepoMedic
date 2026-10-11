from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from repomedic.core.models import Finding, ScanContext, Severity
from repomedic.scanners.base import BaseScanner

JS_LOCKFILES = [
    "package-lock.json",
    "npm-shrinkwrap.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "bun.lockb",
    "bun.lock",
]

JS_APP_INDICATOR_DEPS = {
    "next",
    "nuxt",
    "react-scripts",
    "vite",
    "webpack",
    "express",
    "fastify",
    "@nestjs/core",
    "electron",
    "gatsby",
    "remix",
}

APP_CONFIG_FILES = {
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Procfile",
}


class JsScanner(BaseScanner):
    name = "javascript"
    description = "JavaScript and TypeScript project configuration, dependencies, and lockfile diagnostics"

    def scan(self, context: ScanContext) -> list[Finding]:
        root = context.repo_path
        if not self._is_js_repo(root):
            return []

        findings: list[Finding] = []
        pkg_json = root / "package.json"
        pkg_data: dict[str, Any] = {}

        if pkg_json.exists():
            try:
                pkg_data = json.loads(pkg_json.read_text(encoding="utf-8"))
            except Exception as err:
                findings.append(
                    Finding(
                        code="RM200",
                        message=f"Failed to parse package.json: {err}",
                        severity=Severity.ERROR,
                        file_path="package.json",
                        suggestion="Ensure package.json is valid JSON formatting.",
                    )
                )
                return findings

        findings.extend(self._check_lockfiles(root, pkg_data))
        findings.extend(self._check_dependencies(pkg_data))
        findings.extend(self._check_typescript(root))

        return findings

    def _is_js_repo(self, root: Path) -> bool:
        if (root / "package.json").exists():
            return True
        return (
            any(root.glob("*.js"))
            or any(root.glob("*.ts"))
            or any(root.glob("src/*.js"))
            or any(root.glob("src/*.ts"))
        )

    def _check_lockfiles(self, root: Path, pkg_data: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        found_locks = [lf for lf in JS_LOCKFILES if (root / lf).exists()]

        # Multiple lockfiles
        if len(found_locks) > 1:
            findings.append(
                Finding(
                    code="RM202",
                    message=f"Multiple conflicting package manager lockfiles found: {', '.join(found_locks)}",
                    severity=Severity.WARNING,
                    file_path=found_locks[0],
                    suggestion="Retain a single package manager lockfile to prevent version desynchronization.",
                )
            )

        # Context-aware lockfile missing
        deps = pkg_data.get("dependencies", {})
        dev_deps = pkg_data.get("devDependencies", {})
        all_deps = {**deps, **dev_deps}
        is_private = pkg_data.get("private") is True
        has_app_dep = any(dep in JS_APP_INDICATOR_DEPS for dep in all_deps)
        has_app_file = any((root / f).exists() for f in APP_CONFIG_FILES)

        is_app = is_private or has_app_dep or has_app_file

        if len(found_locks) == 0 and all_deps and is_app:
            findings.append(
                Finding(
                    code="RM201",
                    message="JavaScript/TypeScript application lacks a lockfile (e.g. package-lock.json, pnpm-lock.yaml, yarn.lock)",
                    severity=Severity.WARNING,
                    file_path="package.json",
                    suggestion="Generate and commit a lockfile using npm install, pnpm install, or yarn install.",
                )
            )

        return findings

    def _check_dependencies(self, pkg_data: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        deps_sections = ["dependencies", "devDependencies", "optionalDependencies"]

        for sec in deps_sections:
            deps = pkg_data.get(sec, {})
            if not isinstance(deps, dict):
                continue

            for name, ver in deps.items():
                if not isinstance(ver, str):
                    continue
                ver_clean = ver.strip()

                if ver_clean.startswith("http://"):
                    findings.append(
                        Finding(
                            code="RM204",
                            message=f"Insecure plain HTTP dependency URL for '{name}': {ver_clean}",
                            severity=Severity.ERROR,
                            file_path="package.json",
                            suggestion="Use secure HTTPS URLs or standard package registry versions.",
                        )
                    )

                if ver_clean in ("*", "latest"):
                    findings.append(
                        Finding(
                            code="RM205",
                            message=f"Wildcard or 'latest' dependency version specified for '{name}': {ver_clean}",
                            severity=Severity.WARNING,
                            file_path="package.json",
                            suggestion=f"Pin '{name}' to a specific version or semver range (e.g. ^1.2.0).",
                        )
                    )

        return findings

    def _check_typescript(self, root: Path) -> list[Finding]:
        findings: list[Finding] = []
        has_ts = False

        for ext in ("*.ts", "*.tsx"):
            for p in root.rglob(ext):
                parts = p.parts
                if any(ignored in parts for ignored in ("node_modules", "dist", "build", ".next")):
                    continue
                has_ts = True
                break
            if has_ts:
                break

        if has_ts and not (root / "tsconfig.json").exists():
            findings.append(
                Finding(
                    code="RM203",
                    message="TypeScript files found in project but missing tsconfig.json",
                    severity=Severity.WARNING,
                    file_path="tsconfig.json",
                    suggestion="Create a tsconfig.json file (e.g. via 'npx tsc --init') to configure compiler options.",
                )
            )

        return findings
