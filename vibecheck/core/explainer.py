"""Rich-based terminal output formatter.

Renders vibecheck results as beautiful, structured terminal output.
"""

from __future__ import annotations

import sys

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.markdown import Markdown
from rich import box

from vibecheck.core.severity import Severity, SEVERITY_CONFIG, ICONS, sort_issues, _supports_unicode
from vibecheck.core.detector import Issue

# Force terminal mode to avoid legacy Windows renderer issues with Unicode
console = Console(width=88)


def _severity_panel(title: str, content: str, severity: Severity) -> Panel:
    cfg = SEVERITY_CONFIG[severity]
    return Panel(
        content,
        title=f" {cfg['emoji']} {title} ",
        title_align="left",
        border_style=cfg["panel_border"],
        box=box.ROUNDED,
        width=88,
        padding=(1, 2),
    )


def _format_issue(issue: Issue) -> str:
    lines = [
        f"[bold]{issue.pattern_name}[/bold] -- line {issue.line_number}",
        f"  [dim]{issue.line_content}[/dim]",
        f"  {issue.description}",
        f"  [italic]Fix:[/italic] {issue.fix_hint}",
    ]
    return "\n".join(lines)


def render_file_report(
    filepath: str,
    issues: list[Issue],
    concepts: list[str],
    concept_statuses: dict[str, str],
    llm_response: dict[str, str] | None = None,
    learn_mode: bool = False,
    senior_mode: bool = False,
    risks_mode: bool = False,
) -> None:
    """Render the full vibecheck report for a file."""
    console.print()
    console.rule(f"[bold] vibecheck [/bold] -- {filepath}", style="bright_cyan")
    console.print()

    sorted_issues = sort_issues(issues)
    critical = [i for i in sorted_issues if i.severity == Severity.CRITICAL]
    warnings = [i for i in sorted_issues if i.severity == Severity.WARN]
    infos = [i for i in sorted_issues if i.severity == Severity.INFO]

    # --- CRITICAL (first, always) ---
    if critical:
        content = "\n\n".join(_format_issue(i) for i in critical)
        console.print(_severity_panel("CRITICAL", content, Severity.CRITICAL))
        console.print()

    # --- WHAT THIS CODE DOES ---
    summary = ""
    if llm_response and llm_response.get("summary"):
        summary = llm_response["summary"]
    else:
        summary = f"Analysis of {filepath} -- set an API key for AI-powered summary."

    console.print(Panel(
        summary,
        title=f" {ICONS['book']} WHAT THIS CODE DOES ",
        title_align="left",
        border_style="bright_cyan",
        box=box.ROUNDED,
        width=88,
        padding=(1, 2),
    ))
    console.print()

    # --- WARNINGS ---
    if warnings:
        content = "\n\n".join(_format_issue(i) for i in warnings)
        console.print(_severity_panel("WARNINGS", content, Severity.WARN))
        console.print()

    # --- LLM EXPLANATIONS ---
    if llm_response and llm_response.get("explanations"):
        console.print(Panel(
            Markdown(llm_response["explanations"]),
            title=f" {ICONS['docs']} DETAILS ",
            title_align="left",
            border_style="bright_magenta",
            box=box.ROUNDED,
            width=88,
            padding=(1, 2),
        ))
        console.print()

    # --- CONCEPTS ---
    if concepts:
        concept_lines = []
        for concept in concepts:
            status = concept_statuses.get(concept, "new")
            if status == "learned":
                concept_lines.append(f"  [dim]{ICONS['check']} {concept} -- [LEARNED -- skipping][/dim]")
            elif status == "reminder":
                concept_lines.append(f"  {ICONS['arrow']} {concept} -- [yellow]seen before, quick reminder[/yellow]")
            else:
                concept_lines.append(f"  [bold bright_cyan]{ICONS['star']} {concept}[/bold bright_cyan] -- [bright_green]NEW[/bright_green]")

        concept_text = "\n".join(concept_lines)
        console.print(Panel(
            concept_text,
            title=f" {ICONS['brain']} CONCEPTS IN THIS FILE ",
            title_align="left",
            border_style="bright_blue",
            box=box.ROUNDED,
            width=88,
            padding=(1, 2),
        ))
        console.print()

    # --- INFO ---
    if infos:
        content = "\n\n".join(_format_issue(i) for i in infos)
        console.print(_severity_panel("INFO", content, Severity.INFO))
        console.print()

    # --- SENIOR PERSPECTIVE ---
    if senior_mode and llm_response and llm_response.get("senior"):
        console.print(Panel(
            Markdown(llm_response["senior"]),
            title=f" {ICONS['grad']} WHAT A SENIOR DEV WOULD CHANGE ",
            title_align="left",
            border_style="bright_magenta",
            box=box.ROUNDED,
            width=88,
            padding=(1, 2),
        ))
        console.print()

    # --- RISK ANALYSIS ---
    if risks_mode and llm_response and llm_response.get("risks"):
        console.print(Panel(
            Markdown(llm_response["risks"]),
            title=f" {ICONS['search']} EXTENDED RISK ANALYSIS ",
            title_align="left",
            border_style="red",
            box=box.ROUNDED,
            width=88,
            padding=(1, 2),
        ))
        console.print()

    # --- LOOKS GOOD ---
    if not critical and not warnings:
        console.print(Panel(
            "[bright_green]No critical issues or warnings found.[/bright_green]\n"
            f"Code in {filepath} follows good practices.",
            title=f" {ICONS['check']} LOOKS GOOD ",
            title_align="left",
            border_style="green",
            box=box.ROUNDED,
            width=88,
            padding=(1, 2),
        ))
        console.print()


def render_error_report(
    filepath: str,
    error_message: str,
    llm_response: dict[str, str],
) -> None:
    """Render error diagnosis report."""
    console.print()
    console.rule(f"[bold] vibecheck --error [/bold] -- {filepath}", style="bright_red")
    console.print()

    console.print(Panel(
        llm_response.get("root_cause", "Unable to determine root cause."),
        title=f" {ICONS['search']} ROOT CAUSE ",
        title_align="left",
        border_style="bright_red",
        box=box.ROUNDED,
        width=88,
        padding=(1, 2),
    ))
    console.print()

    if llm_response.get("where_to_look"):
        console.print(Panel(
            llm_response["where_to_look"],
            title=f" {ICONS['pin']} WHERE TO LOOK ",
            title_align="left",
            border_style="yellow",
            box=box.ROUNDED,
            width=88,
            padding=(1, 2),
        ))
        console.print()

    if llm_response.get("concept"):
        console.print(Panel(
            llm_response["concept"],
            title=f" {ICONS['brain']} CONCEPT ",
            title_align="left",
            border_style="bright_blue",
            box=box.ROUNDED,
            width=88,
            padding=(1, 2),
        ))
        console.print()


def render_debt_report(
    total_files: int,
    analyzed_files: int,
    never_analyzed: int,
    critical_results: list[dict],
    llm_response: dict[str, str] | None = None,
) -> None:
    """Render knowledge debt scan report."""
    console.print()
    console.rule("[bold] vibecheck --debt [/bold]", style="bright_yellow")
    console.print()

    # Knowledge gap summary
    gap_text = (
        f"  [bold]{total_files}[/bold] files total\n"
        f"  [bright_green]{analyzed_files}[/bright_green] files analyzed before\n"
        f"  [bright_red]{never_analyzed}[/bright_red] files never analyzed"
    )
    console.print(Panel(
        gap_text,
        title=f" {ICONS['chart']} KNOWLEDGE GAP ",
        title_align="left",
        border_style="bright_yellow",
        box=box.ROUNDED,
        width=88,
        padding=(1, 2),
    ))
    console.print()

    # Critical files -- START HERE
    if critical_results:
        lines = []
        for cr in critical_results:
            issue_names = ", ".join(set(i["pattern_name"] for i in cr["issues"]))
            lines.append(f"  {ICONS['arrow']} [bold]{cr['filepath']}[/bold]")
            lines.append(f"    contains: {issue_names}")
        start_text = "\n".join(lines)

        if llm_response and llm_response.get("critical_files"):
            start_text += f"\n\n{llm_response['critical_files']}"

        console.print(Panel(
            start_text,
            title=f" {ICONS['alert']} START HERE (critical, needs review) ",
            title_align="left",
            border_style="bright_red",
            box=box.ROUNDED,
            width=88,
            padding=(1, 2),
        ))
        console.print()

    # Can wait
    can_wait = llm_response.get("can_wait", "") if llm_response else ""
    if can_wait:
        console.print(Panel(
            can_wait,
            title=f" {ICONS['check']} CAN WAIT ",
            title_align="left",
            border_style="green",
            box=box.ROUNDED,
            width=88,
            padding=(1, 2),
        ))
        console.print()


def render_hook_output(filepath: str, issues: list[Issue]) -> None:
    """Render minimal pre-commit hook output."""
    for issue in issues:
        if issue.severity in (Severity.CRITICAL, Severity.WARN):
            cfg = SEVERITY_CONFIG[issue.severity]
            console.print(
                f"  {cfg['emoji']}  [bold]{filepath}[/bold] -- "
                f"{issue.pattern_name} (line {issue.line_number})"
            )
            console.print(
                f"      run: [cyan]vibecheck {filepath}[/cyan] to understand"
            )


def render_memory_reset(count: int) -> None:
    """Render memory reset confirmation."""
    console.print()
    if count > 0:
        console.print(f"  [bright_green]{ICONS['check']}[/bright_green] Cleared {count} learned concepts from memory.")
    else:
        console.print("  [dim]No concepts in memory to clear.[/dim]")
    console.print()


def render_ai_audit_report(result: object) -> None:
    """Render AI-pattern audit report with confidence scoring."""
    from vibecheck.core.severity import Severity, sort_issues

    console.print()
    console.rule("[bold] vibecheck --ai-audit [/bold] -- Catch what Claude misses", style="bright_magenta")
    console.print()

    # Language scope notice for non-Python files
    if result.language != "python":
        console.print(Panel(
            f"[yellow]AI Audit is currently optimized for Python.[/yellow]\n"
            f"Detected language: [bold]{result.language}[/bold]\n\n"
            "A subset of checks (wildcard imports, placeholder logic) may still apply.\n"
            "Full multi-language AI Audit support is planned for a future release.",
            title=f" {ICONS['book']} LANGUAGE SCOPE ",
            title_align="left",
            border_style="yellow",
            box=box.ROUNDED,
            width=88,
            padding=(1, 2),
        ))
        console.print()

    confidence = result.ai_confidence
    count = result.ai_pattern_count

    # Confidence badge config
    _UNICODE = _supports_unicode()
    conf_config = {
        "HIGH":   ("bright_red",   "!! HIGH",  f"{count} AI anti-patterns -- strong signal of unreviewed AI code"),
        "MEDIUM": ("yellow",       "!! MEDIUM", f"{count} AI anti-patterns -- likely contains AI-generated sections"),
        "LOW":    ("bright_blue",  "i  LOW",   f"{count} AI anti-pattern -- minor signal, worth reviewing"),
        "CLEAN":  ("bright_green", "v  CLEAN", "No AI anti-patterns detected -- code looks well-reviewed"),
    }
    color, badge, summary = conf_config.get(confidence, ("white", "?", "Unknown"))

    console.print(Panel(
        f"[bold]{result.filepath}[/bold]\n\n"
        f"  AI Confidence: [{color}]  {badge}  [/{color}]\n"
        f"  {summary}",
        title=f" {ICONS['brain']} AI AUDIT RESULT ",
        title_align="left",
        border_style=color,
        box=box.ROUNDED,
        width=88,
        padding=(1, 2),
    ))
    console.print()

    if not result.ai_issues:
        console.print(Panel(
            "[bright_green]No AI-pattern anti-patterns found.[/bright_green]\n"
            "This code does not exhibit the typical failure patterns of AI-generated code.",
            title=f" {ICONS['check']} ALL CLEAR ",
            title_align="left",
            border_style="bright_green",
            box=box.ROUNDED,
            width=88,
            padding=(1, 2),
        ))
        console.print()
        return

    # Sort and group issues
    sorted_issues = sort_issues(result.ai_issues)
    critical = [i for i in sorted_issues if i.severity == Severity.CRITICAL]
    warnings  = [i for i in sorted_issues if i.severity == Severity.WARN]
    infos     = [i for i in sorted_issues if i.severity == Severity.INFO]

    groups = [
        (critical, "CRITICAL AI PATTERNS", "bright_red"),
        (warnings,  "AI ANTI-PATTERNS",     "yellow"),
        (infos,     "AI CODE SMELLS",        "bright_blue"),
    ]
    for group, label, group_color in groups:
        if group:
            content = "\n\n".join(_format_issue(i) for i in group)
            console.print(Panel(
                content,
                title=f" {ICONS['search']} {label} ",
                title_align="left",
                border_style=group_color,
                box=box.ROUNDED,
                width=88,
                padding=(1, 2),
            ))
            console.print()

    # "Why Claude Misses These" educational panel
    pattern_names = ", ".join(sorted({i.pattern_name for i in result.ai_issues}))
    console.print(Panel(
        f"[dim]Patterns found: {pattern_names}\n\n"
        "Claude, Copilot, and ChatGPT optimize for code that [italic]looks[/italic] correct.\n"
        "They do not run your code, simulate execution order, or validate against production constraints.\n\n"
        "VibeCheck uses deterministic rules — same code, same result, every time.\n"
        "It also knows your team's custom standards via [bold].vibecheck_rules.md[/bold],\n"
        "and remembers what you have already learned so it never repeats itself.[/dim]",
        title=f" {ICONS['grad']} WHY CLAUDE MISSES THESE ",
        title_align="left",
        border_style="dim",
        box=box.ROUNDED,
        width=88,
        padding=(1, 2),
    ))
    console.print()

