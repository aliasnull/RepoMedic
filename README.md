# RepoMedic 🩺

[![CI](https://github.com/repomedic/repomedic/actions/workflows/ci.yml/badge.svg)](https://github.com/repomedic/repomedic/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](pyproject.toml)

**RepoMedic** is a fast, offline-first repository diagnostics toolkit for Python and JavaScript/TypeScript projects. It audits repository hygiene, dependency health, configurations, and sensitive credential leaks without requiring network access, paid APIs, or mandatory authentication.

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
git clone https://github.com/your-org/repomedic.git
cd repomedic
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

# Fail CI only if errors are found (exit code 1)
repomedic scan . --fail-on error

# Fail CI if any warning or error is found
repomedic scan . --fail-on warning
```

### Exit Codes

- `0`: Scan completed cleanly (or findings were below the `--fail-on` threshold).
- `1`: Diagnostics reported issues meeting or exceeding the `--fail-on` threshold.
- `2`: Invalid CLI arguments or non-existent path.

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

Add RepoMedic to your workflow (`.github/workflows/diagnostics.yml`):

```yaml
name: Diagnostics

on: [push, pull_request]

jobs:
  repomedic:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: repomedic/repomedic@v1
        with:
          path: '.'
          format: 'github'
          fail-on: 'error'
```

---

## 🧪 Running Tests

Run the test suite using `pytest`:

```bash
pytest -v
```

---

## 📄 License

Licensed under the [Apache License, Version 2.0](LICENSE).
