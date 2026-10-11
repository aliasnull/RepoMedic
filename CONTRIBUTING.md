# Contributing to RepoMedic

Thank you for your interest in contributing to RepoMedic! We welcome issues, documentation improvements, diagnostic rule proposals, and pull requests.

RepoMedic is an offline-first, zero-runtime-dependency repository diagnostics toolkit for Python and JavaScript/TypeScript projects.

---

## Code of Conduct

All contributors and participants are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please report unacceptable behavior following the guidelines therein.

---

## Architecture & Design Principles

Before making changes, keep these core principles in mind:

1. **Zero External Runtime Dependencies:** RepoMedic uses only the Python standard library. Do not add runtime dependencies to `dependencies` in `pyproject.toml`.
2. **Offline-First & Private:** Scanners must never perform outbound network requests, query external APIs, or transmit repository code.
3. **Deterministic & Fast:** Diagnostics should run locally in milliseconds.
4. **Context-Aware:** Scanners should distinguish between deployable applications and distributed libraries where appropriate.
5. **Rule Organization:**
   - `RM001`–`RM099`: General repository hygiene, git tracking, and sensitive leak detection ([`repomedic.scanners.repo.RepoScanner`](repomedic/scanners/repo.py)).
   - `RM100`–`RM199`: Python configuration, dependencies, and lockfiles ([`repomedic.scanners.python.PythonScanner`](repomedic/scanners/python.py)).
   - `RM200`–`RM299`: JavaScript and TypeScript configuration, dependencies, and lockfiles ([`repomedic.scanners.js.JsScanner`](repomedic/scanners/js.py)).

---

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git

### Getting the Code

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/aliasnull/RepoMedic.git
   cd RepoMedic
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install RepoMedic in editable mode with development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

---

## Running Tests and Diagnostics

Run the full automated test suite:
```bash
pytest -v
```

Run dogfooding diagnostics on the RepoMedic repository itself:
```bash
repomedic scan .
```
Or run directly via module invocation:
```bash
python3 -m repomedic scan .
```

Verify Action security regression tests:
```bash
pytest tests/test_action_security.py -v
```

---

## Adding a Diagnostic Rule

When contributing a new diagnostic rule:

1. Inherit from `BaseScanner` in [`repomedic/scanners/base.py`](repomedic/scanners/base.py) or extend the appropriate existing scanner.
2. Define a unique rule code adhering to the `RMxxx` namespace and set an appropriate `Severity` (`INFO`, `WARNING`, or `ERROR`).
3. Include an actionable suggestion string explaining how to fix the finding.
4. Add comprehensive unit tests in the `tests/` directory verifying positive detection, negative cases, and edge cases.
5. Document the rule in [README.md](README.md) under the Diagnostic Rules Reference.

---

## Submitting Pull Requests

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/my-new-rule
   ```
2. Commit your changes with clear, descriptive commit messages.
3. Ensure all tests and diagnostics pass:
   ```bash
   pytest -v
   repomedic scan . --fail-on warning
   ```
4. Push your branch to your fork and open a Pull Request against `main`. Fill out the pull request template completely.
