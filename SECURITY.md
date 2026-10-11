# Security Policy

RepoMedic takes the security and privacy of its users seriously. As a diagnostic tool designed to detect credential leaks and configuration issues, we are committed to maintaining a secure, private, and offline-first foundation.

---

## Supported Versions

Only the latest release branch receives security updates and bug fixes:

| Version | Supported |
| :--- | :--- |
| `0.1.x` | :white_check_mark: |
| `< 0.1.0` | :x: |

---

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability, sensitive pattern leak flaw, or security bypass in RepoMedic:

1. **GitHub Security Advisory (Preferred):** Open a draft advisory through [GitHub Security Advisories](https://github.com/aliasnull/RepoMedic/security/advisories/new).
2. **Alternative Contact:** If the advisory interface is unavailable, contact the repository maintainers directly via their GitHub profile ([@aliasnull](https://github.com/aliasnull)).

### What to Include in Your Report

To help triage and resolve the issue effectively, please provide:
- A description of the vulnerability and its potential impact.
- Clear reproduction steps, proof-of-concept repository structure, or minimal code snippet.
- The version of RepoMedic and Python runtime environment.
- Any proposed mitigations or fixes, if available.

### Response & Remediation

Maintainers endeavor to review and triage vulnerability reports promptly. Confirmed vulnerabilities will be addressed in a subsequent patch release, accompanied by an advisory attribution if desired.

---

## Security Principles & Architecture

RepoMedic is built on strict security guarantees:

1. **Zero Outbound Network Calls:** RepoMedic never uploads repository contents, code, or detected tokens over the network. All scanning runs locally.
2. **Zero Runtime Dependencies:** Built purely on the Python standard library to eliminate supply-chain dependency vulnerabilities.
3. **GitHub Action Hardening:** The composite action (`action.yml`) strictly passes inputs via shell environment variables rather than direct `${{ inputs... }}` string interpolation to protect against command injection attacks.
