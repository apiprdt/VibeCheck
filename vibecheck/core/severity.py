"""Severity levels for detected issues."""

import os
import sys
from enum import Enum


class Severity(str, Enum):
    """Issue severity levels, ordered by importance."""

    CRITICAL = "CRITICAL"
    WARN = "WARN"
    INFO = "INFO"


def _supports_unicode() -> bool:
    """Check if the terminal supports unicode/emoji output."""
    # Headless CI runners often fail with complex emojis
    if os.environ.get("GITHUB_ACTIONS"):
        return False
    try:
        if sys.platform == "win32":
            # Try encoding a test emoji — if it fails, use ASCII
            try:
                "🚨".encode(sys.stdout.encoding or "utf-8")
                return True
            except (UnicodeEncodeError, LookupError):
                return False
        return True
    except Exception:
        return False


_UNICODE = _supports_unicode()

# Display configuration for Rich output
SEVERITY_CONFIG = {
    Severity.CRITICAL: {
        "emoji": "!!" if not _UNICODE else "🚨",
        "color": "red",
        "style": "bold red",
        "panel_border": "bright_red",
        "title": "CRITICAL",
    },
    Severity.WARN: {
        "emoji": "/!\\" if not _UNICODE else "⚠️",
        "color": "yellow",
        "style": "bold yellow",
        "panel_border": "yellow",
        "title": "WARNINGS",
    },
    Severity.INFO: {
        "emoji": "(i)" if not _UNICODE else "💡",
        "color": "blue",
        "style": "bold blue",
        "panel_border": "blue",
        "title": "INFO",
    },
}

# Emoji/ASCII alternatives for section headers
ICONS = {
    "book": "[i]" if not _UNICODE else "📖",
    "brain": "[*]" if not _UNICODE else "🧠",
    "search": "[?]" if not _UNICODE else "🔍",
    "pin": "[>]" if not _UNICODE else "📍",
    "chart": "[#]" if not _UNICODE else "📊",
    "grad": "[^]" if not _UNICODE else "🎓",
    "docs": "[=]" if not _UNICODE else "📚",
    "alert": "!!" if not _UNICODE else "🚨",
    "check": "[v]" if not _UNICODE else "✓",
    "star": "*" if not _UNICODE else "★",
    "arrow": "->" if not _UNICODE else "→",
}


def sort_issues(issues: list) -> list:
    """Sort issues by severity: CRITICAL first, then WARN, then INFO."""
    severity_order = {Severity.CRITICAL: 0, Severity.WARN: 1, Severity.INFO: 2}
    return sorted(issues, key=lambda i: severity_order.get(i.severity, 99))
