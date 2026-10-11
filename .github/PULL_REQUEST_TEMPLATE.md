## Summary of Changes

<!-- Briefly describe the purpose and scope of your changes -->

## Related Issue

<!-- Link to any related issue or rule proposal, e.g. Fixes #123 -->

## Type of Change

- [ ] Bug fix (non-breaking change fixing an issue or false positive)
- [ ] New diagnostic rule (RMxxx)
- [ ] Scanner enhancement (Python, JavaScript/TypeScript, or Repo)
- [ ] Documentation update
- [ ] CI / Workflow / Community file update

## Contributor Checklist

- [ ] My code adheres to RepoMedic's zero-runtime-dependency design (Python stdlib only).
- [ ] I have added or updated unit tests covering all new logic in `tests/`.
- [ ] All automated tests pass: `pytest -v`.
- [ ] Repository self-diagnostics pass cleanly: `repomedic scan .` (or `python3 -m repomedic scan .`).
- [ ] Documentation (such as `README.md` rule tables or CLI options) has been updated accordingly.
- [ ] I have read and agree to follow the [Code of Conduct](../CODE_OF_CONDUCT.md) and [Contributing Guidelines](../CONTRIBUTING.md).
