from __future__ import annotations

from abc import ABC, abstractmethod
from repomedic.core.models import DiagnosticResult


class BaseReporter(ABC):
    @abstractmethod
    def format(self, result: DiagnosticResult) -> str:
        """Format the diagnostic result into a string."""
        raise NotImplementedError
