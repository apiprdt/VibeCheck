"""vibecheck CLI -- Understand the code your AI wrote.

Entry point for all vibecheck commands.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from vibecheck import __version__
from vibecheck.core.detector import detect, detect_fast, DetectionResult
from vibecheck.core.severity import Severity, sort_issues
from vibecheck.core.memory import (
    get_memory_context, record_concept, reset_memory, get_all_concepts,
)
from vibecheck.core.explainer import (
    render_file_report, render_error_report, render_debt_report,
    render_memory_reset, render_hook_output, console as rich_console,
)
from vibecheck.core.llm import explain_issues, explain_error, analyze_debt, is_llm_available, _load_config

app = typer.Typer(
    name="vibecheck",
    help="Understand the code your AI wrote.",
    add_completion=False,
    no_args_is_help=True,
)
err_console = Console(stderr=True)

# Supported file extensions for scanning
SCAN_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs",
    ".java", ".rb", ".php", ".c", ".cpp", ".cs",
}


def _version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        rich_console.print(f"vibecheck {__version__}")
        raise typer.Exit()


def _format_issues_for_llm(issues: list) -> str:
    """Format issues as text for the LLM prompt."""
    if not issues:
        return ""
    lines = []
    for issue in issues:
        lines.append(
            f"- [{issue.severity.value}] {issue.pattern_name} "
            f"(line {issue.line_number}): {issue.description}"
        )
    return "\n".join(lines)


def _should_ignore_file(filepath: str, config: dict) -> bool:
    """Check if file should be ignored based on config."""
    import fnmatch
    ignore_files = config.get("ignore_files", [])
    for pattern in ignore_files:
        if fnmatch.fnmatch(filepath, pattern) or fnmatch.fnmatch(Path(filepath).name, pattern):
            return True
    return False


def _filter_issues(issues: list, config: dict) -> list:
    """Filter out issues matching ignore_patterns from config."""
    ignore_patterns = config.get("ignore_patterns", [])
    if not ignore_patterns:
        return issues
    return [i for i in issues if i.pattern_name not in ignore_patterns]


def _output_json(result, concept_statuses: dict = None) -> None:
    """Print detection results as JSON for CI/CD integration."""
    output = {
        "filepath": result.filepath,
        "language": result.language,
        "issues": [
            {
                "pattern": i.pattern_name,
                "severity": i.severity.value,
                "line": i.line_number,
                "code": i.line_content,
                "description": i.description,
                "fix": i.fix_hint,
            }
            for i in result.issues
        ],
        "concepts": result.concepts,
        "summary": {
            "critical": sum(1 for i in result.issues if i.severity == Severity.CRITICAL),
            "warn": sum(1 for i in result.issues if i.severity == Severity.WARN),
            "info": sum(1 for i in result.issues if i.severity == Severity.INFO),
            "total": len(result.issues),
        },
    }
    if concept_statuses:
        output["concept_statuses"] = concept_statuses
    print(json.dumps(output, indent=2))


@app.command()
def main(
    file: Optional[str] = typer.Argument(None, help="File or directory to analyze"),
    error: Optional[str] = typer.Option(
        None, "--error", "-e", help="Error message to diagnose"
    ),
    debt: Optional[str] = typer.Option(
        None, "--debt", "-d", help="Directory to scan for knowledge debt"
    ),
    learn: bool = typer.Option(False, "--learn", help="Deeper concept explanations with examples"),
    senior: bool = typer.Option(False, "--senior", help="Add senior dev perspective"),
    risks: bool = typer.Option(False, "--risks", help="Add extended risk analysis"),
    install_hook: bool = typer.Option(False, "--install-hook", help="Install git pre-commit hook"),
    fail_on_critical: bool = typer.Option(
        False, "--fail-on-critical", help="Hook blocks on critical issues"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON (for CI/CD)"),
    reset_mem: bool = typer.Option(False, "--reset-memory", help="Clear all learned concepts"),
    version: bool = typer.Option(
        False, "--version", "-v", help="Show version", callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Analyze code files for issues, concepts, and learning opportunities."""

    # --- Reset memory ---
    if reset_mem:
        count = reset_memory()
        render_memory_reset(count)
        return

    # --- Install hook ---
    if install_hook:
        from vibecheck.hooks.pre_commit import install_hook as do_install
        do_install(fail_on_critical=fail_on_critical)
        return

    # --- Debt scan ---
    if debt:
        _run_debt_scan(debt)
        return

    # --- Need a file from here ---
    if not file:
        rich_console.print("[red]Error:[/red] Please provide a file to analyze.")
        rich_console.print("  Usage: [cyan]vibecheck <file>[/cyan]")
        raise typer.Exit(1)

    filepath = Path(file)
    if not filepath.exists():
        rich_console.print(f"[red]Error:[/red] File not found: {file}")
        raise typer.Exit(1)

    # --- Error diagnosis ---
    if error:
        _run_error_diagnosis(str(filepath), error)
        return

    # --- Core file analysis ---
    _run_file_analysis(
        str(filepath), learn=learn, senior=senior, risks=risks,
        json_output=json_output,
    )


def _run_file_analysis(
    filepath: str,
    learn: bool = False,
    senior: bool = False,
    risks: bool = False,
    json_output: bool = False,
) -> None:
    """Core vibecheck command: analyze a single file."""
    # Load config
    config = _load_config()

    # Check if file should be ignored
    if _should_ignore_file(filepath, config):
        if not json_output:
            rich_console.print(f"[dim]Skipping {filepath} (ignored in config)[/dim]")
        return

    # Step 1: Rule-based detection
    try:
        result = detect(filepath)
    except FileNotFoundError:
        rich_console.print(f"[red]Error:[/red] File not found: {filepath}")
        raise typer.Exit(1)
    except Exception as e:
        rich_console.print(f"[red]Error reading file:[/red] {e}")
        raise typer.Exit(1)

    # Filter issues based on config
    result.issues = _filter_issues(result.issues, config)

    # Apply severity filter from config
    severity_filter = config.get("severity_filter", "").lower()
    if severity_filter == "critical":
        result.issues = [i for i in result.issues if i.severity == Severity.CRITICAL]
    elif severity_filter == "warn":
        result.issues = [i for i in result.issues if i.severity in (Severity.CRITICAL, Severity.WARN)]

    # Step 2: Check concept memory
    concept_statuses = get_memory_context(result.concepts)

    # Step 3: LLM explanation (if available)
    llm_response = None
    if is_llm_available():
        try:
            code = Path(filepath).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            code = Path(filepath).read_text(encoding="latin-1")

        issues_text = _format_issues_for_llm(result.issues)
        llm_response = explain_issues(
            code=code,
            issues_text=issues_text,
            concepts=result.concepts,
            memory_context=concept_statuses,
            filepath=filepath,
            learn_mode=learn,
            senior_mode=senior,
            risks_mode=risks,
        )

    # Step 4: Update concept memory
    for concept in result.concepts:
        record_concept(concept, filepath)

    # Step 5: Render output
    if json_output:
        _output_json(result, concept_statuses)
        return

    render_file_report(
        filepath=filepath,
        issues=result.issues,
        concepts=result.concepts,
        concept_statuses=concept_statuses,
        llm_response=llm_response,
        learn_mode=learn,
        senior_mode=senior,
        risks_mode=risks,
    )


def _run_error_diagnosis(filepath: str, error_message: str) -> None:
    """Diagnose an error message in context of a file."""
    try:
        code = Path(filepath).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        code = Path(filepath).read_text(encoding="latin-1")
    except FileNotFoundError:
        rich_console.print(f"[red]Error:[/red] File not found: {filepath}")
        raise typer.Exit(1)

    # Always run rule-based detection first as fallback context
    try:
        result = detect(filepath)
    except Exception:
        result = None

    if not is_llm_available():
        rich_console.print()
        rich_console.print("[yellow]No LLM API key configured.[/yellow]")
        rich_console.print(
            "  Set one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, or OLLAMA_API_BASE"
        )
        rich_console.print(
            "  Showing rule-based analysis instead:\n"
        )
        # Fall back to regular file analysis
        if result and (result.issues or result.concepts):
            concept_statuses = get_memory_context(result.concepts)
            render_file_report(
                filepath=filepath,
                issues=result.issues,
                concepts=result.concepts,
                concept_statuses=concept_statuses,
            )
        return

    llm_response = explain_error(
        code=code,
        error_message=error_message,
        filepath=filepath,
    )

    render_error_report(
        filepath=filepath,
        error_message=error_message,
        llm_response=llm_response,
    )


def _run_debt_scan(directory: str) -> None:
    """Scan a directory for knowledge debt."""
    dir_path = Path(directory)
    if not dir_path.is_dir():
        rich_console.print(f"[red]Error:[/red] Not a directory: {directory}")
        raise typer.Exit(1)

    # Collect all scannable files
    all_files = []
    for ext in SCAN_EXTENSIONS:
        all_files.extend(dir_path.rglob(f"*{ext}"))

    # Filter out common non-source directories
    skip_dirs = {
        "node_modules", ".git", "__pycache__", ".venv", "venv",
        "dist", "build", ".next", ".nuxt", "vendor",
    }
    all_files = [
        f for f in all_files
        if not any(part in skip_dirs for part in f.parts)
    ]
    all_files.sort()

    if not all_files:
        rich_console.print(f"[yellow]No source files found in {directory}[/yellow]")
        raise typer.Exit(0)

    total_files = len(all_files)

    # Check which files have been analyzed (concepts exist for them)
    known_concepts = get_all_concepts()
    known_files = {c["last_file"] for c in known_concepts if c.get("last_file")}
    analyzed = sum(1 for f in all_files if str(f) in known_files)
    never_analyzed = total_files - analyzed

    # Scan all files for issues
    file_summaries = []
    critical_results = []
    clean_results = []

    for fpath in all_files:
        try:
            result = detect_fast(str(fpath))
            summary = {
                "filepath": str(fpath),
                "language": result.language,
                "issues": [
                    {
                        "pattern_name": i.pattern_name,
                        "line_number": i.line_number,
                        "severity": i.severity.value,
                    }
                    for i in result.issues
                ],
            }
            file_summaries.append(summary)

            has_critical = any(i.severity == Severity.CRITICAL for i in result.issues)
            if has_critical:
                critical_results.append(summary)
            elif not result.issues:
                clean_results.append(summary)
        except Exception:
            pass

    # LLM analysis (if available)
    llm_response = None
    if is_llm_available() and file_summaries:
        llm_response = analyze_debt(file_summaries, total_files, analyzed)
    elif clean_results:
        # Without LLM, build a basic "CAN WAIT" list from clean files
        can_wait_lines = []
        for cr in clean_results[:10]:
            can_wait_lines.append(
                f"  {cr['filepath']} ({cr['language']}, no issues detected)"
            )
        llm_response = {
            "critical_files": "",
            "can_wait": "\n".join(can_wait_lines),
        }

    render_debt_report(
        total_files=total_files,
        analyzed_files=analyzed,
        never_analyzed=never_analyzed,
        critical_results=critical_results,
        llm_response=llm_response,
    )


if __name__ == "__main__":
    app()
