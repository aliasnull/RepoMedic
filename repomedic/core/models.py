from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

    def _rank(self) -> int:
        ranks = {"INFO": 1, "WARNING": 2, "ERROR": 3}
        return ranks.get(self.value, 0)

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, Severity):
            return self._rank() < other._rank()
        return NotImplemented

    def __le__(self, other: Any) -> bool:
        if isinstance(other, Severity):
            return self._rank() <= other._rank()
        return NotImplemented

    def __gt__(self, other: Any) -> bool:
        if isinstance(other, Severity):
            return self._rank() > other._rank()
        return NotImplemented

    def __ge__(self, other: Any) -> bool:
        if isinstance(other, Severity):
            return self._rank() >= other._rank()
        return NotImplemented


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    severity: Severity
    file_path: Optional[str] = None
    line: Optional[int] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line": self.line,
            "suggestion": self.suggestion,
        }


@dataclass
class ScanContext:
    repo_path: Path
    is_git_repo: bool = False
    tracked_files: set[str] = field(default_factory=set)

    def is_tracked(self, rel_path: str) -> bool:
        norm = rel_path.replace("\\", "/").strip("./")
        return norm in self.tracked_files


@dataclass
class DiagnosticResult:
    findings: list[Finding] = field(default_factory=list)
    duration_ms: float = 0.0
    scanned_files_count: int = 0

    @property
    def has_errors(self) -> bool:
        return any(f.severity == Severity.ERROR for f in self.findings)

    @property
    def has_warnings(self) -> bool:
        return any(f.severity == Severity.WARNING for f in self.findings)

    def counts_by_severity(self) -> dict[str, int]:
        counts = {"ERROR": 0, "WARNING": 0, "INFO": 0}
        for f in self.findings:
            counts[f.severity.value] = counts.get(f.severity.value, 0) + 1
        return counts

    def filter_by_min_severity(self, min_severity: Severity) -> list[Finding]:
        return [f for f in self.findings if f.severity >= min_severity]

    def to_dict(self) -> dict[str, Any]:
        return {
            "findings": [f.to_dict() for f in self.findings],
            "counts": self.counts_by_severity(),
            "scanned_files_count": self.scanned_files_count,
            "duration_ms": self.duration_ms,
            "has_errors": self.has_errors,
            "has_warnings": self.has_warnings,
        }
