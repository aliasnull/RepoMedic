# RepoMedic 🩺

[![CI](https://github.com/aliasnull/RepoMedic/actions/workflows/ci.yml/badge.svg)](https://github.com/aliasnull/RepoMedic/actions/workflows/ci.yml)
[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-RepoMedic-blue.svg?logo=github)](https://github.com/marketplace/actions/repomedic-repository-diagnostics)
[![Latest Release](https://img.shields.io/github/v/release/aliasnull/RepoMedic)](https://github.com/aliasnull/RepoMedic/releases/latest)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](pyproject.toml)

**RepoMedic** is a fast, offline-first repository diagnostics toolkit for Python and JavaScript/TypeScript projects. It audits repository hygiene, dependency health, configurations, and sensitive credential leaks without requiring network access, paid APIs, or mandatory authentication.

---

## ❓ The Problem RepoMedic Solves

Modern software repositories often break in CI or leak credentials due to subtle oversights:
- **Missing or unpinned dependencies:** Causing non-deterministic deployment failures.
- **Accidental secret exposure:** Staged or committed `.env` files, API keys, or private keys.
- **Configuration omissions:** Missing `.gitignore`, licenses, or compiler configs (`tsconfig.json`).
- **Heavy or SaaS-dependent linters:** Many diagnostic tools require Docker, Node.js plus Python runtimes, external API keys, or paid subscriptions.

**RepoMedic solves this by being:**
1. **Offline-First:** No outbound network calls. All checks run locally and deterministically.
2. **Zero Runtime Dependencies:** Pure Python standard library implementation compatible with Python 3.10+.
3. **Instant:** Scans standard repositories in ~30 milliseconds.
4. **Context-Aware:** Understands the difference between deployable applications and distributed libraries.

---

## ✨ Features

- **⚡ Zero Runtime Dependencies:** Built purely on the Python standard library with Python 3.10+ compatibility (using built-in or fallback TOML parsing).
- **🔒 Offline-First & Private:** Never makes outbound network requests, never uploads code, never requires an account or API key.
- **🛡️ Sensitive Leak Detection:** Finds committed `.env` files, private keys, and high-entropy credentials while filtering out false positives from `.env.example` templates and test fixtures.
- **📦 Context-Aware Lockfile Diagnostics:** Understands the difference between application repositories (which require lockfiles for reproducible builds) and libraries.
- **🌐 Polyglot Diagnostics:** Deep checks for Python (`requirements.txt`, `pyproject.toml`) and JS/TS (`package.json`, `tsconfig.json`, lockfiles).
- **🚀 CI & GitHub Actions Native:** Supports colored terminal output, machine-readable JSON, and GitHub Actions workflow commands (`::error::`, `::warning::`, `$GITHUB_STEP_SUMMARY`).

---

## 🚀 Quickstart

### Installation

Clone the repository and install RepoMedic locally:

```bash
git clone https://github.com/aliasnull/RepoMedic.git
cd RepoMedic
pip install -e .
```

Or run directly using Python without installation:

```bash
python3 -m repomedic scan .
```

---

## 💻 CLI Usage

```bash
# Scan current repository (default console output)
repomedic scan .

# Output machine-readable JSON
repomedic scan . --format json

# Output GitHub Actions workflow commands and summary
repomedic scan . --format github

# Run without ANSI colors
repomedic scan . --no-color

# Fail CI only if errors are found (exit code 1)
repomedic scan . --fail-on error

# Fail CI if any warning or error is found
repomedic scan . --fail-on warning

# Check CLI version
repomedic --version
```

### Exit Codes

- `0`: Scan completed cleanly (or findings were below the `--fail-on` threshold).
- `1`: Diagnostics reported issues meeting or exceeding the `--fail-on` threshold.
- `2`: Invalid CLI arguments or non-existent path.

---

## 📊 JSON Output Schema

When `--format json` is specified, RepoMedic produces deterministic, structured output suitable for automated pipelines:

```json
{
  "findings": [
    {
      "code": "RM001",
      "message": "Missing .gitignore file",
      "severity": "WARNING",
      "file_path": ".gitignore",
      "line": null,
      "suggestion": "Add a .gitignore file tailored to your languages and frameworks."
    }
  ],
  "counts": {
    "ERROR": 0,
    "WARNING": 1,
    "INFO": 0
  },
  "scanned_files_count": 32,
  "duration_ms": 28.5,
  "has_errors": false,
  "has_warnings": true
}
```

---

## 📋 Diagnostic Rules Reference

| Code | Severity | Description | Category |
| :--- | :--- | :--- | :--- |
| **RM001** | `WARNING` | Missing `.gitignore` file | Repo Hygiene |
| **RM002** | `INFO` | Missing `README.md` documentation file | Repo Hygiene |
| **RM003** | `INFO` | Missing `LICENSE` file | Repo Hygiene |
| **RM004** | `ERROR` / `WARNING` | Potentially exposed sensitive file (`.env`, `.pem`, private key) | Security |
| **RM005** | `ERROR` | Potential hardcoded secret or token detected in code | Security |
| **RM100** | `ERROR` | Failed to parse `pyproject.toml` | Python Config |
| **RM101** | `WARNING` | Python application missing dependency lockfile (`uv.lock`, `poetry.lock`, etc.) | Dependencies |
| **RM102** | `WARNING` / `INFO` | Unpinned dependency version in `requirements.txt` | Dependencies |
| **RM103** | `WARNING` | `pyproject.toml` defines `[project]` but missing `[build-system]` table | Python Config |
| **RM104** | `INFO` | Missing `project.requires-python` runtime specification | Python Config |
| **RM105** | `ERROR` | Insecure plain HTTP package index or dependency URL | Security |
| **RM200** | `ERROR` | Failed to parse `package.json` | JS/TS Config |
| **RM201** | `WARNING` | JS/TS application missing package lockfile (`package-lock.json`, etc.) | Dependencies |
| **RM202** | `WARNING` | Multiple conflicting package manager lockfiles detected | Dependencies |
| **RM203** | `WARNING` | TypeScript files found but missing `tsconfig.json` configuration | TypeScript |
| **RM204** | `ERROR` | Insecure plain HTTP dependency URL in `package.json` | Security |
| **RM205** | `WARNING` | Wildcard `*` or `latest` dependency version used | Dependencies |

---

## 🤖 GitHub Actions Integration

Use RepoMedic directly in your GitHub Actions workflows via the composite action ([`action.yml`](action.yml)):

```yaml
name: Diagnostics

on: [push, pull_request]

jobs:
  repomedic:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Run RepoMedic
        uses: aliasnull/RepoMedic@v0.1.2
        with:
          path: '.'
          format: 'github'
          fail-on: 'error'
          python-version: '3.11'
```

### Action Inputs

| Input | Description | Default |
| :--- | :--- | :--- |
| `path` | Path to repository or directory to scan | `.` |
| `format` | Output format (`console`, `json`, `github`) | `github` |
| `fail-on` | Failure threshold (`error`, `warning`, `none`) | `error` |
| `python-version` | Python version for the setup step | `3.11` |

---

## ⚠️ Limitations (v1 Scope)

- **Static & Offline Only:** RepoMedic does not make outbound network queries to online vulnerability databases (e.g., OSV, CVE, NVD).
- **Rule-Based:** Secret detection uses regex patterns and known file indicators rather than full semantic analysis.
- **No Web Dashboard:** v1 is intentionally designed as a lightweight CLI and CI tool without a web UI or background daemon.

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for full developer setup instructions, scanner guidelines, and pull request procedures.

1. Fork and clone the repository (`git clone https://github.com/aliasnull/RepoMedic.git && cd RepoMedic`).
2. Install in editable mode with test dependencies: `pip install -e ".[dev]"`.
3. Run the automated test suite: `pytest -v`.
4. Ensure new rules follow the existing `BaseScanner` interface and include tests.
5. Submit a pull request following our [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md).

For vulnerability disclosure, please see our [Security Policy](SECURITY.md). All contributors are expected to uphold our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## 📄 License

Licensed under the [Apache License, Version 2.0](LICENSE).
