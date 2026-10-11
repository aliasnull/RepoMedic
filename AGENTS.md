# AGENTS.md — token-frugal working rules

## Context hygiene
- New task = new session; compact/summarize when context grows heavy.
- Read only the files you need; prefer search/grep over reading whole files.
- Never re-read a file that has not changed since you last read it.

## Scope discipline
- Make minimal, surgical changes; do not touch files outside the task.
- For anything beyond a small edit: present a short plan first, then execute.

## Execution
- Run targeted tests, not the whole suite, unless asked.
- If an installed skill covers the task, use it and follow its scripts
  instead of re-deriving steps.
- Keep diffs, comments and answers concise; no boilerplate.
