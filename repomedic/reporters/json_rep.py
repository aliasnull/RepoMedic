from __future__ import annotations

import json
from repomedic.core.models import DiagnosticResult
from repomedic.reporters.base import BaseReporter


class JsonReporter(BaseReporter):
    def __init__(self, indent: int = 2) -> None:
        self.indent = indent

    def format(self, result: DiagnosticResult) -> str:
        return json.dumps(result.to_dict(), indent=self.indent)
