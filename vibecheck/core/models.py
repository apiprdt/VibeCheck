from __future__ import annotations
from dataclasses import dataclass, field
from vibecheck.core.severity import Severity

@dataclass
class Issue:
    """A detected code issue."""

    pattern_name: str
    severity: Severity
    line_number: int
    line_content: str
    description: str
    fix_hint: str
    is_ai_pattern: bool = False  # True for patterns common in AI-generated code


@dataclass
class DetectionResult:
    """Complete detection result for a file."""

    filepath: str
    language: str
    issues: list[Issue] = field(default_factory=list)
    concepts: list[str] = field(default_factory=list)


@dataclass
class AIAuditResult:
    """Detection result for AI-generated code pattern audit."""

    filepath: str
    language: str
    ai_issues: list[Issue] = field(default_factory=list)

    @property
    def ai_confidence(self) -> str:
        """Confidence level that this is AI-generated code."""
        count = len(self.ai_issues)
        if count >= 4:
            return "HIGH"
        elif count >= 2:
            return "MEDIUM"
        elif count >= 1:
            return "LOW"
        return "CLEAN"

    @property
    def ai_pattern_count(self) -> int:
        return len(self.ai_issues)
