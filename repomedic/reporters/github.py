from __future__ import annotations

import os
from pathlib import Path
from repomedic.core.models import DiagnosticResult, Severity
from repomedic.reporters.base import BaseReporter


class GitHubReporter(BaseReporter):
    def format(self, result: DiagnosticResult) -> str:
        lines: list[str] = []

        for f in result.findings:
            if f.severity == Severity.ERROR:
                cmd = "error"
            elif f.severity == Severity.WARNING:
                cmd = "warning"
            else:
                cmd = "notice"

            params: list[str] = []
            if f.file_path:
                params.append(f"file={f.file_path}")
            if f.line is not None:
                params.append(f"line={f.line}")
            params.append(f"title={f.code}")

            param_str = f" {','.join(params)}" if params else ""
            lines.append(f"::{cmd}{param_str}::{f.message}")

        # Also write GITHUB_STEP_SUMMARY if available
        summary_env = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_env:
            try:
                summary_path = Path(summary_env)
                counts = result.counts_by_severity()
                summary_md = [
                    "### RepoMedic Diagnostic Summary\n",
                    f"- **Scanned Files:** {result.scanned_files_count}",
                    f"- **Duration:** {result.duration_ms:.1f}ms\n",
                    "| Severity | Count |",
                    "| :--- | :--- |",
                    f"| Error | {counts.get('ERROR', 0)} |",
                    f"| Warning | {counts.get('WARNING', 0)} |",
                    f"| Info | {counts.get('INFO', 0)} |\n",
                ]
                if result.findings:
                    summary_md.append("| Code | Severity | Location | Message | Suggestion |")
                    summary_md.append("| :--- | :--- | :--- | :--- | :--- |")
                    for f in result.findings:
                        loc = f.file_path or "-"
                        if f.line:
                            loc += f":{f.line}"
                        sug = f.suggestion or "-"
                        summary_md.append(f"| {f.code} | {f.severity.value} | `{loc}` | {f.message} | {sug} |")

                with summary_path.open("a", encoding="utf-8") as f:
                    f.write("\n".join(summary_md) + "\n")
            except Exception:
                pass

        return "\n".join(lines)
