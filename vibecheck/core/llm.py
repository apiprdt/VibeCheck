"""LiteLLM wrapper for AI-powered code explanations.

LLM is used ONLY for explanation — never for detection.
Detection is always rule-based (see detector.py).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

SYSTEM_PROMPT = """You are vibecheck, a professional code education assistant.
Your role is to explain code and teach concepts clearly.

Tone rules:
- Always formal and professional
- CRITICAL issues: firm and direct, include fix example
- Warnings: clear and actionable
- Teaching: patient, contextual, never condescending
- Never imply the developer is incompetent
- Never say "your AI generated this"
- If code is good: say so explicitly first
- Max 3-5 sentences per concept explanation
- Always include code example when showing a fix

You will receive:
- The code file content
- A list of issues already detected (rule-based)
- A list of concepts found in the file
- Memory context: which concepts user has already learned

Your job: explain the detected issues and teach the new concepts. Do not re-detect issues."""

# Config file path
CONFIG_PATH = Path.home() / ".vibecheck" / "config.yaml"


def _load_config() -> dict:
    """Load config from ~/.vibecheck/config.yaml if it exists."""
    if CONFIG_PATH.exists():
        try:
            import yaml
            with open(CONFIG_PATH, "r") as f:
                config = yaml.safe_load(f)
            return config if isinstance(config, dict) else {}
        except Exception:
            return {}
    return {}


def get_model() -> str:
    """Get the configured LLM model.

    Priority: VIBECHECK_MODEL env var > config.yaml > default.
    """
    env_model = os.environ.get("VIBECHECK_MODEL")
    if env_model:
        return env_model

    config = _load_config()
    if config.get("model"):
        return config["model"]

    return "gpt-4o-mini"


def is_llm_available() -> bool:
    """Check if any LLM API key is configured."""
    return any(os.environ.get(v) for v in [
        "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OLLAMA_API_BASE",
    ])


def _call_llm(messages: list[dict[str, str]], **kwargs: Any) -> str:
    """Make a completion call via LiteLLM.

    Returns the response text, or an error message if the call fails.
    """
    try:
        import litellm
        litellm.suppress_debug_info = True
        response = litellm.completion(
            model=get_model(),
            messages=messages,
            max_tokens=2000,
            temperature=0.3,
            **kwargs,
        )
        return response.choices[0].message.content.strip()
    except ImportError:
        return "[LLM unavailable -- litellm not installed]"
    except Exception as e:
        error_msg = str(e)
        # Provide helpful error messages for common issues
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            return "[LLM error: Invalid or missing API key. Check your OPENAI_API_KEY or ANTHROPIC_API_KEY.]"
        if "rate_limit" in error_msg.lower():
            return "[LLM error: Rate limit reached. Wait a moment and try again.]"
        if "connection" in error_msg.lower():
            return f"[LLM error: Cannot connect to API. Check your network. ({error_msg})]"
        return f"[LLM call failed: {error_msg}]"


def _parse_sections(response: str, keys: list[tuple[str, str]]) -> dict[str, str]:
    """Parse ### delimited sections from LLM response."""
    result = {k: "" for _, k in keys}
    sections = response.split("###")
    for section in sections:
        s = section.strip()
        low = s.lower()
        for prefix, key in keys:
            if low.startswith(prefix):
                result[key] = s.split("\n", 1)[-1].strip() if "\n" in s else ""
                break
    return result


def explain_issues(
    code: str, issues_text: str, concepts: list[str],
    memory_context: dict[str, str], filepath: str,
    learn_mode: bool = False, senior_mode: bool = False, risks_mode: bool = False,
) -> dict[str, str]:
    """Get LLM explanations for detected issues and concepts.

    Returns dict with keys: summary, explanations, senior, risks.
    """
    if not is_llm_available():
        return {"summary": "", "explanations": "", "senior": "", "risks": ""}

    concept_lines = []
    for c in concepts:
        status = memory_context.get(c, "new")
        if status == "learned":
            concept_lines.append(f"- {c}: [LEARNED -- skip]")
        elif status == "reminder":
            concept_lines.append(f"- {c}: [SEEN ONCE -- one-line reminder]")
        else:
            depth = "5-8 sentences" if learn_mode else "3-5 sentences"
            concept_lines.append(f"- {c}: [NEW -- explain in {depth}]")

    prompt = (
        f"Analyze: {filepath}\n\n```\n{code[:6000]}\n```\n\n"
        f"## Detected Issues:\n{issues_text or 'None.'}\n\n"
        f"## Concepts:\n{chr(10).join(concept_lines) or 'None.'}\n\n"
        "Respond with:\n### SUMMARY\n(3-5 sentences)\n### EXPLANATIONS\n(issues + concepts)"
    )
    if senior_mode:
        prompt += "\n### SENIOR PERSPECTIVE\n(architecture suggestions)"
    if risks_mode:
        prompt += "\n### RISK ANALYSIS\n(production risks)"

    resp = _call_llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ])
    result = _parse_sections(resp, [
        ("summary", "summary"), ("explanation", "explanations"),
        ("senior", "senior"), ("risk", "risks"),
    ])
    if not result["summary"] and not result["explanations"]:
        result["summary"] = resp
    return result


def explain_error(code: str, error_message: str, filepath: str) -> dict[str, str]:
    """Get LLM explanation for an error message in context.

    Returns dict with keys: root_cause, where_to_look, concept.
    """
    if not is_llm_available():
        return {
            "root_cause": "[Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or OLLAMA_API_BASE for AI-powered diagnosis]",
            "where_to_look": "",
            "concept": "",
        }

    prompt = (
        f"A developer hit this error in {filepath}:\n\n"
        f"Error: {error_message}\n\n"
        f"Code:\n```\n{code[:6000]}\n```\n\n"
        "Provide:\n"
        "### ROOT CAUSE\n1-2 most likely causes. Plain English.\n"
        "### WHERE TO LOOK\nSpecific line(s) to check and why.\n"
        "### CONCEPT\nOne core concept this error reveals. Explain as a mentor would."
    )
    resp = _call_llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ])
    result = _parse_sections(resp, [
        ("root", "root_cause"), ("where", "where_to_look"), ("concept", "concept"),
    ])
    if not result["root_cause"]:
        result["root_cause"] = resp
    return result


def analyze_debt(file_summaries: list[dict[str, Any]], total: int, analyzed: int) -> dict[str, str]:
    """Get LLM analysis for knowledge debt scan.

    Returns dict with keys: critical_files, can_wait.
    """
    if not is_llm_available():
        return {"critical_files": "", "can_wait": ""}

    lines = []
    for fs in file_summaries[:30]:
        issues = ", ".join(
            f"{i['pattern_name']}(L{i['line_number']})" for i in fs.get("issues", [])
        ) or "clean"
        lines.append(f"- {fs['filepath']} [{fs['language']}]: {issues}")

    prompt = (
        f"Debt scan: {total} total, {analyzed} analyzed, {total-analyzed} never analyzed.\n\n"
        + "\n".join(lines)
        + "\n\n### START HERE\nCritical files first.\n### CAN WAIT\nLow-risk files."
    )
    resp = _call_llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ])
    result = _parse_sections(resp, [("start", "critical_files"), ("can", "can_wait")])
    if not result["critical_files"]:
        result["critical_files"] = resp
    return result
