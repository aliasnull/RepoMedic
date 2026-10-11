from __future__ import annotations

from abc import ABC, abstractmethod
from repomedic.core.models import Finding, ScanContext


class BaseScanner(ABC):
    name: str = "base"
    description: str = "Base scanner"

    @abstractmethod
    def scan(self, context: ScanContext) -> list[Finding]:
        """Perform diagnostic scan and return a list of findings."""
        raise NotImplementedError
