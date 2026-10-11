from __future__ import annotations

from repomedic.core.models import DiagnosticResult, Severity
from repomedic.reporters.base import BaseReporter

# ANSI Color Codes
COLOR_RESET = "\033[0m"
COLOR_RED = "\033[31m"
COLOR_YELLOW = "\033[33m"
COLOR_BLUE = "\033[34m"
COLOR_BOLD = "\033[1m"
COLOR_GRAY = "\033[90m"


class ConsoleReporter(BaseReporter):
    def __init__(self, use_color: bool = True) -> None:
        self.use_color = use_color

    def _color(self, text: str, color_code: str) -> str:
        if not self.use_color:
            return text
        return f"{color_code}{text}{COLOR_RESET}"

    def format(self, result: DiagnosticResult) -> str:
        lines: list[str] = []

        if not result.findings:
            lines.append(self._color("✓ All repository diagnostics passed! No issues detected.", COLOR_BOLD))
            lines.append(f"Scanned {result.scanned_files_count} files in {result.duration_ms:.1f}ms.")
            return "\n".join(lines)

        lines.append(self._color("RepoMedic Diagnostic Report", COLOR_BOLD))
        lines.append("-" * 40)

        for finding in result.findings:
            if finding.severity == Severity.ERROR:
                badge = self._color("[ERROR]", COLOR_RED)
            elif finding.severity == Severity.WARNING:
                badge = self._color("[WARNING]", COLOR_YELLOW)
            else:
                badge = self._color("[INFO]", COLOR_BLUE)

            loc = ""
            if finding.file_path:
                loc = f" {finding.file_path}"
                if finding.line is not None:
                    loc += f":{finding.line}"

            lines.append(f"{badge} {self._color(finding.code, COLOR_BOLD)}{loc}: {finding.message}")
            if finding.suggestion:
                lines.append(f"    {self._color('Fix:', COLOR_GRAY)} {finding.suggestion}")

        lines.append("-" * 40)
        counts = result.counts_by_severity()
        summary = (
            f"Errors: {counts.get('ERROR', 0)} | "
            f"Warnings: {counts.get('WARNING', 0)} | "
            f"Info: {counts.get('INFO', 0)} | "
            f"Scanned {result.scanned_files_count} files ({result.duration_ms:.1f}ms)"
        )
        lines.append(summary)

        return "\n".join(lines)
