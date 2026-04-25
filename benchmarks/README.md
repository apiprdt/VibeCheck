# VibeCheck Detection Coverage

VibeCheck's core engine uses deterministic, rule-based pattern matching. Unlike LLMs that produce probabilistic output, VibeCheck returns the **exact same result every time** it runs against the same code.

This page documents exactly what VibeCheck detects and at what severity level.

---

## Security Vulnerability Coverage

Every security pattern references the relevant **CWE** (Common Weakness Enumeration) and **OWASP Top 10** category.

| Pattern | Language(s) | Severity | Reference |
| :--- | :--- | :---: | :--- |
| **SQL Injection** (f-string, .format, concat) | Python, JS, Go | CRITICAL | CWE-89 / OWASP A03:2021 |
| **Hardcoded Credentials** | All | CRITICAL | CWE-798 / OWASP A07:2021 |
| **Code Injection** (`eval()`) | Python, JS | CRITICAL | CWE-94 / OWASP A03:2021 |
| **XSS** (`innerHTML`, `dangerouslySetInnerHTML`) | JS, TSX | CRITICAL | CWE-79 / OWASP A03:2021 |
| **Path Traversal** | Python, JS | CRITICAL | CWE-22 / OWASP A01:2021 |
| **Insecure Deserialization** (`pickle`, `yaml.load`) | Python | CRITICAL | CWE-502 / OWASP A08:2021 |
| **Auth Middleware Order** (Express) | JS, TS | CRITICAL | CWE-862 |
| **Race Condition** (goroutine shared state) | Go | CRITICAL | CWE-362 |
| **SSRF** (user input in HTTP URL) | Python, JS | WARN | CWE-918 / OWASP A10:2021 |
| **Swallowed Errors** (`except: pass`) | Python, JS, Go | WARN | CWE-390 |
| **Missing Timeout** (HTTP/DB clients) | Python, JS, Go | WARN | CWE-400 |
| **SELECT * in SQL** | All | WARN | — |

---

## AI-Generated Code Anti-Patterns (`--ai-audit`)

These patterns are statistically over-represented in code produced by AI assistants (Copilot, ChatGPT, Claude). Currently optimized for **Python**.

| Pattern | Severity | What It Catches |
| :--- | :---: | :--- |
| **Mutable Default Argument** | CRITICAL | `def foo(items=[])` — shared state across calls |
| **Missing Await** | CRITICAL | Async coroutine called without `await` |
| **Shell Injection** (`os.system()`) | CRITICAL | Shell command execution without subprocess |
| **Wildcard Import** | WARN | `from module import *` — namespace pollution |
| **Blocking Call in Async** | WARN | `time.sleep()` or `requests.get()` inside `async def` |
| **Unimplemented Method** | WARN | `raise NotImplementedError` in non-abstract code |
| **Placeholder Logic** | INFO | `# TODO` / `# FIXME` markers left in code |
| **Assert for Validation** | INFO | `assert` used for runtime input checking |
| **Debug Print Statement** | INFO | `print()` in files that already import `logging` |

---

## Code Quality Checks

| Pattern | Language(s) | Severity |
| :--- | :--- | :---: |
| **Missing Type Hints** | Python | INFO |
| **Long Functions** (>50 lines) | All | INFO |
| **Missing Docstrings** | Python | INFO |
| **Magic Numbers** | Python, JS | WARN |

---

## Why Determinism Matters

When you ask an LLM to review code, it reads the code probabilistically. It might notice a SQL injection today, but miss it tomorrow if the prompt changes or the surrounding code is complex.

VibeCheck's rule-based engine (`--fast` mode) is **deterministic**. If a pattern exists in your code, VibeCheck finds it — every time, guaranteed.

We use LLMs *only* for what they are best at: **explaining the problem and teaching the developer how to fix it.**

## Reproducing These Results

All detection patterns are tested in our open test suite:

```bash
# Run all 110 tests
pytest tests/ -v

# Run security detection tests only
pytest tests/test_detector.py -v

# Run AI-pattern tests only
pytest tests/test_ai_audit.py -v
```
