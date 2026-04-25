"""LiteLLM wrapper for AI-powered code explanations.

LLM is used ONLY for explanation — never for detection.
Detection is always rule-based (see detector.py).
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

from vibecheck.core.cache import cache

SYSTEM_PROMPT = """You are VibeCheck, the ultimate safety net for "vibe coders" (developers who heavily use AI to generate code and just want to know if it works).
Your role is to protect them from "Hallucination Debt" without being a boring, judgmental linter.

Tone rules:
- Be a helpful, protective friend, NOT a condescending teacher.
- Use "Consequence-First" language. Don't just say "SQL Injection", say "Someone can type a weird username and delete your entire database."
- Keep it extremely punchy. Short sentences.
- Never say "your AI generated this". Say "The code has a bug..."
- If the code is good, hype them up.
- Provide a "Vibe Dictionary" for technical terms: explain them in ONE simple, relatable sentence (e.g., "SQL Injection: When a user tricks your database into running their text as a command.")

You will receive:
- The code file content
- A list of issues already detected (rule-based)
- A list of concepts found in the file
- Memory context: which concepts user has already learned

Your job: explain the detected issues in "vibe coder" language (consequences first) and provide simple fixes."""


# Config file path
CONFIG_PATH = Path.home() / ".vibecheck" / "config.yaml"


def load_config() -> dict:
    """Load config from .vibecheck/config.yaml (local) or ~/.vibecheck/config.yaml (global)."""
    local_config = Path(".vibecheck/config.yaml")
    paths = [local_config, CONFIG_PATH]
    
    for p in paths:
        if p.exists():
            try:
                import yaml
                with open(p, "r") as f:
                    config = yaml.safe_load(f)
                return config if isinstance(config, dict) else {}
            except Exception:
                continue
    return {}


def get_model() -> str:
    """Get the configured LLM model.

    Priority: VIBECHECK_MODEL env var > config.yaml > default.
    Enterprise Mode: Forces 'ollama/' prefix.
    """
    is_enterprise = os.environ.get("VIBECHECK_ENTERPRISE_MODE") == "1"
    env_model = os.environ.get("VIBECHECK_MODEL")
    
    if env_model:
        model = env_model
    else:
        config = load_config()
        model = config.get("model")
        
        # Smart Defaulting based on available keys
        if not model:
            if os.environ.get("GROQ_API_KEY"):
                model = "groq/llama3-8b-8192"
            elif os.environ.get("ANTHROPIC_API_KEY"):
                model = "claude-3-5-sonnet-20240620"
            elif os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"):
                model = "gemini/gemini-1.5-pro"
            elif os.environ.get("MISTRAL_API_KEY"):
                model = "mistral/mistral-large-latest"
            else:
                model = "gpt-4o-mini"
        
    if is_enterprise and not model.startswith("ollama/"):
        return f"ollama/{model}"
        
    return model


def is_llm_available() -> bool:
    """Check if any LLM API key is configured.
    
    In Enterprise Mode, ONLY Ollama is allowed.
    Supports OpenAI, Anthropic, Google (Gemini), Mistral, and Ollama.
    """
    if os.environ.get("VIBECHECK_ENTERPRISE_MODE") == "1":
        return bool(os.environ.get("OLLAMA_API_BASE"))
        
    return any(os.environ.get(v) for v in [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
        "MISTRAL_API_KEY",
        "OLLAMA_API_BASE",
        "GEMINI_API_KEY",
        "GROQ_API_KEY",
    ])


def _call_llm(messages: list[dict[str, str]], **kwargs: Any) -> str:
    """Make a completion call via LiteLLM.

    Returns the response text, or an error message if the call fails.
    """
    try:
        import litellm
        litellm.suppress_debug_info = True
        
        # Handle Ollama base URL if provided
        api_base = os.environ.get("OLLAMA_API_BASE")
        if api_base:
            kwargs["api_base"] = api_base

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
            return f"[LLM error: Invalid or missing API key. (Literal error: {error_msg})]"
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

    # Check for Project Specific Guidelines with Monorepo Support (Hierarchical)
    project_rules = ""
    current_dir = Path(filepath).resolve().parent
    rules_files = []
    
    # Traverse up to 5 levels to find rules (stops at .git)
    for _ in range(5):
        rules_path = current_dir / ".vibecheck_rules.md"
        if rules_path.exists():
            rules_files.append(rules_path)
        if current_dir.parent == current_dir or (current_dir / ".git").exists():
            break
        current_dir = current_dir.parent
        
    # Combine rules from top-level to local-level
    combined_rules = []
    for r_path in reversed(rules_files):
        try:
            with open(r_path, "r", encoding="utf-8") as f:
                combined_rules.append(f"--- Rules from {r_path.parent.name}/{r_path.name} ---\n" + f.read())
        except Exception:
            pass
            
    raw_rules = "\n\n".join(combined_rules)
    if raw_rules:
        # SAFETY 1: Token Limit Safeguard (Max ~1000 tokens / 4000 chars)
        if len(raw_rules) > 4000:
            project_rules = raw_rules[:4000] + "\n\n[WARNING: .vibecheck_rules.md files are too large and were truncated.]"
        else:
            project_rules = raw_rules
            
        # SAFETY 2: Basic Language Filter
        ext = Path(filepath).suffix
        if ext in [".py"]:
            project_rules = f"(Priority: Focus on Python/Backend rules)\n{project_rules}"
        elif ext in [".js", ".jsx", ".ts", ".tsx"]:
            project_rules = f"(Priority: Focus on Javascript/Frontend rules)\n{project_rules}"


    # Check Cache first
    cache_key = {
        "code_hash": hashlib.md5(code.encode()).hexdigest(),
        "issues": issues_text,
        "modes": [learn_mode, senior_mode, risks_mode],
        "project_rules_hash": hashlib.md5(project_rules.encode()).hexdigest() if project_rules else "",
        "model": get_model()
    }
    cached_resp = cache.get(**cache_key)
    if cached_resp:
        return cached_resp

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
        f"## Detected Issues (Global):\n{issues_text or 'None.'}\n\n"
        f"## Concepts:\n{chr(10).join(concept_lines) or 'None.'}\n\n"
    )
    
    if project_rules:
        prompt += f"## PROJECT-SPECIFIC GUIDELINES:\n{project_rules}\n(Ensure the code follows these local rules. If not, point it out as a CRITICAL/WARN issue!)\n\n"

    prompt += "Respond with:\n### SUMMARY\n(3-5 sentences)\n### EXPLANATIONS\n(issues + concepts)"
    
    if learn_mode:
        prompt += "\n\n[ABSOLUTE BEGINNER MODE ACTIVE]\n"
        prompt += "1. Explain all issues and concepts using SIMPLE REAL-WORLD ANALOGIES (e.g., a restaurant, a house, a locked door).\n"
        prompt += "2. Assume the user has ZERO computer science background. DO NOT use technical jargon like 'SQL Injection', 'AST', or 'Middleware' without explaining what it means in everyday language.\n"
        prompt += "3. Always provide a tiny, clear 'Before (Bad)' and 'After (Good)' code example.\n"
        
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
    
    # Store in Cache
    cache.set(result, **cache_key)
    
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

    # Check Cache
    cache_key = {
        "debt_summaries": file_summaries[:30], # Cache based on top 30 files
        "total": total,
        "analyzed": analyzed,
        "model": get_model()
    }
    cached_resp = cache.get(**cache_key)
    if cached_resp:
        return cached_resp

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
    
    # Store in Cache
    cache.set(result, **cache_key)
    
    return result
