"""Git pre-commit hook integration.

Installs and runs a pre-commit hook that uses rule-based
detection only (no LLM) for fast scanning under 2 seconds.
"""

from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

from rich.console import Console

from vibecheck.core.detector import detect_fast
from vibecheck.core.severity import Severity, ICONS

console = Console(width=88, force_terminal=True)

HOOK_SCRIPT_TEMPLATE = '''#!/usr/bin/env bash
# vibecheck pre-commit hook
# Scans staged files for critical issues (rule-based only, no LLM)
# Override with: git commit --no-verify

python -m vibecheck.hooks.pre_commit {fail_flag}
exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo ""
    echo "vibecheck: commit blocked due to critical issues."
    echo "Override with: git commit --no-verify"
    exit 1
fi
'''

HOOK_SCRIPT_TEMPLATE_WIN = '''@echo off
REM vibecheck pre-commit hook
REM Scans staged files for critical issues (rule-based only, no LLM)
REM Override with: git commit --no-verify

python -m vibecheck.hooks.pre_commit {fail_flag}
if errorlevel 1 (
    echo.
    echo vibecheck: commit blocked due to critical issues.
    echo Override with: git commit --no-verify
    exit /b 1
)
'''


def install_hook(fail_on_critical: bool = False) -> None:
    """Install vibecheck as a git pre-commit hook."""
    # Find .git directory
    try:
        git_root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("[red]Error:[/red] Not inside a git repository.")
        return

    hooks_dir = Path(git_root) / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    hook_path = hooks_dir / "pre-commit"
    fail_flag = "--fail-on-critical" if fail_on_critical else ""

    # Check if hook already exists
    if hook_path.exists():
        content = hook_path.read_text()
        if "vibecheck" in content:
            console.print("[yellow]vibecheck hook already installed.[/yellow]")
            return
        else:
            console.print(f"[yellow]{ICONS['alert']}  Existing pre-commit hook found.[/yellow]")
            console.print("  Backing up to pre-commit.backup")
            backup = hooks_dir / "pre-commit.backup"
            hook_path.rename(backup)

    # Write hook script
    if sys.platform == "win32":
        hook_path_win = hooks_dir / "pre-commit"
        hook_path_win.write_text(
            HOOK_SCRIPT_TEMPLATE.format(fail_flag=fail_flag)
        )
        # Also write a .cmd version for Windows
        hook_cmd = hooks_dir / "pre-commit.cmd"
        hook_cmd.write_text(
            HOOK_SCRIPT_TEMPLATE_WIN.format(fail_flag=fail_flag)
        )
    else:
        hook_path.write_text(
            HOOK_SCRIPT_TEMPLATE.format(fail_flag=fail_flag)
        )

    # Make executable
    hook_path.chmod(hook_path.stat().st_mode | stat.S_IEXEC)

    console.print()
    console.print(f"[bright_green]{ICONS['check']} vibecheck pre-commit hook installed.[/bright_green]")
    if fail_on_critical:
        console.print("  [yellow]Mode: commits will be BLOCKED on critical issues.[/yellow]")
    else:
        console.print("  Mode: warnings only (commits not blocked).")
    console.print("  Override any time with: [cyan]git commit --no-verify[/cyan]")
    console.print()


def run_hook(fail_on_critical: bool = False) -> int:
    """Run the pre-commit hook scan on staged files.

    Returns:
        0 if no issues or not blocking, 1 if blocking on critical.
    """
    # Get staged files
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True, text=True, check=True,
        )
        staged_files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return 0

    if not staged_files:
        return 0

    # Supported extensions
    supported = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java"}
    scannable = [f for f in staged_files if Path(f).suffix in supported]

    if not scannable:
        return 0

    console.print()
    console.rule("[bold]vibecheck pre-commit scan[/bold]", style="bright_cyan")
    console.print()

    has_critical = False

    for filepath in scannable:
        if not Path(filepath).exists():
            continue
        try:
            detection = detect_fast(filepath)
            critical_warn = [
                i for i in detection.issues
                if i.severity in (Severity.CRITICAL, Severity.WARN)
            ]
            if critical_warn:
                from vibecheck.core.explainer import render_hook_output
                render_hook_output(filepath, critical_warn)
                if any(i.severity == Severity.CRITICAL for i in critical_warn):
                    has_critical = True
        except Exception:
            pass

    if has_critical:
        console.print()
        if fail_on_critical:
            console.print("[red]Commit blocked — critical issues found.[/red]")
            console.print("Override with: [cyan]git commit --no-verify[/cyan]")
            console.print()
            return 1
        else:
            console.print(f"[yellow]Committing... {ICONS['check']} (not blocked)[/yellow]")
    else:
        console.print(f"[bright_green]Committing... {ICONS['check']} (no issues)[/bright_green]")

    console.print()
    return 0


if __name__ == "__main__":
    fail_flag = "--fail-on-critical" in sys.argv
    exit_code = run_hook(fail_on_critical=fail_flag)
    sys.exit(exit_code)
