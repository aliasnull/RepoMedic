from __future__ import annotations

import os
from pathlib import Path
from repomedic.core.models import DiagnosticResult, Severity
from repomedic.reporters.base import BaseReporter


def _escape_workflow_data(val: str) -> str:
    """Escape data for GitHub Actions workflow command message."""
    return val.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _escape_markdown_table_cell(val: str) -> str:
    """Escape data for GitHub Step Summary Markdown table cell."""
    return val.replace("|", "\\|").replace("\r\n", "<br>").replace("\n", "<br>")


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
            escaped_msg = _escape_workflow_data(f.message)
            lines.append(f"::{cmd}{param_str}::{escaped_msg}")

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
                        safe_msg = _escape_markdown_table_cell(f.message)
                        safe_sug = _escape_markdown_table_cell(sug)
                        safe_loc = _escape_markdown_table_cell(loc)
                        summary_md.append(
                            f"| {f.code} | {f.severity.value} | `{safe_loc}` | {safe_msg} | {safe_sug} |"
                        )

                with summary_path.open("a", encoding="utf-8") as out:
                    out.write("\n".join(summary_md) + "\n")
            except Exception:
                pass

        return "\n".join(lines)
