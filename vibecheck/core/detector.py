"""Rule-based pattern detection for code issues.

This module handles ALL issue detection. LLM is never used for detection —
only for explanation after issues are found.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from vibecheck.core.severity import Severity

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

LANG_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".rb": "ruby",
    ".php": "php",
    ".c": "c",
    ".cpp": "cpp",
    ".cs": "csharp",
}


def detect_language(filepath: str) -> str:
    """Detect programming language from file extension."""
    ext = Path(filepath).suffix.lower()
    return LANG_MAP.get(ext, "unknown")


# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

# --- CRITICAL patterns ---

def _check_sql_injection(lines: list[str], language: str) -> list[Issue]:
    """Detect f-string or string concatenation inside SQL queries."""
    issues = []
    sql_keywords = re.compile(
        r"(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)",
        re.IGNORECASE,
    )
    # Python f-string SQL injection
    fstring_sql = re.compile(
        r'f["\'].*\{.*\}.*(?:SELECT|INSERT|UPDATE|DELETE|DROP|WHERE|FROM)',
        re.IGNORECASE,
    )
    # String format SQL injection
    format_sql = re.compile(
        r'["\'].*(?:SELECT|INSERT|UPDATE|DELETE|DROP|WHERE|FROM).*["\'].*\.format\(',
        re.IGNORECASE,
    )
    # String concatenation in SQL
    concat_sql = re.compile(
        r'["\'].*(?:SELECT|INSERT|UPDATE|DELETE|DROP|WHERE|FROM).*["\']\s*\+',
        re.IGNORECASE,
    )
    # % formatting SQL injection
    percent_sql = re.compile(
        r'["\'].*(?:SELECT|INSERT|UPDATE|DELETE|DROP|WHERE|FROM).*%s.*["\']\s*%',
        re.IGNORECASE,
    )

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if fstring_sql.search(stripped):
            issues.append(Issue(
                pattern_name="SQL Injection",
                severity=Severity.CRITICAL,
                line_number=i,
                line_content=stripped,
                description="User input interpolated directly into SQL query via f-string. "
                            "An attacker can inject arbitrary SQL commands.",
                fix_hint='Use parameterized queries: cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))  [CWE-89 / OWASP A03:2021]',
            ))
        elif format_sql.search(stripped):
            issues.append(Issue(
                pattern_name="SQL Injection",
                severity=Severity.CRITICAL,
                line_number=i,
                line_content=stripped,
                description="User input interpolated into SQL via .format(). "
                            "An attacker can inject arbitrary SQL commands.",
                fix_hint='Use parameterized queries: cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))  [CWE-89 / OWASP A03:2021]',
            ))
        elif concat_sql.search(stripped):
            issues.append(Issue(
                pattern_name="SQL Injection",
                severity=Severity.CRITICAL,
                line_number=i,
                line_content=stripped,
                description="User input concatenated into SQL string. "
                            "An attacker can inject arbitrary SQL commands.",
                fix_hint='Use parameterized queries: cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))  [CWE-89 / OWASP A03:2021]',
            ))

    # Also check multi-line context: execute() call with f-string nearby
    full_text = "\n".join(lines)
    execute_fstring = re.compile(
        r'\.execute\s*\(\s*f["\']', re.IGNORECASE
    )
    for match in execute_fstring.finditer(full_text):
        line_num = full_text[:match.start()].count("\n") + 1
        line_content = lines[line_num - 1].strip() if line_num <= len(lines) else ""
        # Avoid duplicate if already flagged
        if not any(iss.line_number == line_num and iss.pattern_name == "SQL Injection" for iss in issues):
            issues.append(Issue(
                pattern_name="SQL Injection",
                severity=Severity.CRITICAL,
                line_number=line_num,
                line_content=line_content,
                description="f-string used directly in .execute() call. "
                            "An attacker can inject arbitrary SQL commands.",
                fix_hint='Use parameterized queries: cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))',
            ))

    return issues


def _check_hardcoded_credentials(lines: list[str], language: str) -> list[Issue]:
    """Detect hardcoded passwords, secrets, API keys, tokens."""
    issues = []
    pattern = re.compile(
        r"""(?:password|passwd|secret|api_key|apikey|api_secret|token|auth_token|access_token|private_key)"""
        r"""\s*[=:]\s*['"][^'"]{3,}['"]""",
        re.IGNORECASE,
    )
    # Exclude obvious test/example patterns
    exclude = re.compile(r"(example|placeholder|your[_-]|<|TODO|CHANGEME|xxx)", re.IGNORECASE)

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*"):
            continue
        match = pattern.search(stripped)
        if match and not exclude.search(match.group(0)):
            issues.append(Issue(
                pattern_name="Hardcoded Credentials",
                severity=Severity.CRITICAL,
                line_number=i,
                line_content=stripped,
                description="Credentials appear to be hardcoded in source code. "
                            "These will be visible in version control history and to anyone with repo access.",
                fix_hint="Use environment variables: os.environ.get('API_KEY') or a secrets manager.  [CWE-798 / OWASP A07:2021]",
            ))

    return issues


def _check_code_injection(lines: list[str], language: str) -> list[Issue]:
    """Detect eval() with non-literal arguments."""
    issues = []
    eval_pattern = re.compile(r'\beval\s*\(')
    safe_eval = re.compile(r'eval\s*\(\s*["\']')  # eval("literal") is less dangerous

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//"):
            continue
        if eval_pattern.search(stripped) and not safe_eval.search(stripped):
            issues.append(Issue(
                pattern_name="Code Injection",
                severity=Severity.CRITICAL,
                line_number=i,
                line_content=stripped,
                description="eval() with dynamic input allows arbitrary code execution. "
                            "An attacker can run any code on your system.",
                fix_hint="Use ast.literal_eval() for safe evaluation, or restructure to avoid eval entirely.  [CWE-94 / OWASP A03:2021]",
            ))

    return issues


def _check_race_condition_go(lines: list[str], language: str) -> list[Issue]:
    """Detect potential race conditions in Go: shared variable accessed in goroutine without mutex."""
    if language != "go":
        return []

    issues = []
    full_text = "\n".join(lines)

    # Check for goroutine with shared variable access and no mutex lock
    has_mutex_lock = bool(re.search(r'\.Lock\(\)', full_text))
    has_goroutine = bool(re.search(r'\bgo\s+\w+', full_text))

    if has_goroutine and not has_mutex_lock:
        # Find package-level variables that are modified
        pkg_vars = set()
        var_pattern = re.compile(r'^var\s+(\w+)\s+', re.MULTILINE)
        for m in var_pattern.finditer(full_text):
            pkg_vars.add(m.group(1))

        # Check if goroutine functions modify package-level variables
        for var_name in pkg_vars:
            # Look for increment, assignment, or modification of the variable
            modify_pattern = re.compile(
                rf'\b{re.escape(var_name)}\s*(?:\+\+|--|[+\-*/]?=)',
            )
            for i, line in enumerate(lines, 1):
                if modify_pattern.search(line):
                    issues.append(Issue(
                        pattern_name="Race Condition",
                        severity=Severity.CRITICAL,
                        line_number=i,
                        line_content=line.strip(),
                        description=f"Variable '{var_name}' is modified in a goroutine without mutex protection. "
                                    "Concurrent access will cause data races and unpredictable behavior.",
                        fix_hint=f"Protect with sync.Mutex: mu.Lock(); {var_name}++; mu.Unlock() "
                                 "or use atomic operations: atomic.AddInt64(&counter, 1)",
                    ))
                    break  # One issue per variable

    return issues


def _check_middleware_order(lines: list[str], language: str) -> list[Issue]:
    """Detect Express.js routes registered before auth middleware."""
    if language not in ("javascript", "typescript"):
        return []

    issues = []
    route_pattern = re.compile(r'app\.(get|post|put|delete|patch)\s*\(')
    middleware_pattern = re.compile(r'app\.use\s*\(.*(?:auth|middleware|protect|guard|verify)', re.IGNORECASE)

    first_route_line = None
    first_route_num = None
    middleware_line_num = None

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if route_pattern.search(stripped) and first_route_line is None:
            first_route_line = stripped
            first_route_num = i
        if middleware_pattern.search(stripped):
            middleware_line_num = i

    if first_route_num and middleware_line_num and first_route_num < middleware_line_num:
        issues.append(Issue(
            pattern_name="Auth Middleware Order",
            severity=Severity.CRITICAL,
            line_number=first_route_num,
            line_content=first_route_line,
            description="Route handler is registered BEFORE auth middleware. "
                        "Express executes middleware in order — this route is unprotected.",
            fix_hint="Move app.use(authMiddleware) ABOVE all route handlers that need protection.",
        ))

    return issues


# --- WARN patterns ---

def _check_swallowed_errors(lines: list[str], language: str) -> list[Issue]:
    """Detect except: pass or except Exception: pass."""
    issues = []

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Check for bare except or except Exception followed by pass
        if re.match(r'except\s*(?:Exception)?\s*(?:as\s+\w+)?\s*:', stripped):
            # Look ahead for 'pass' as the only statement
            for j in range(i, min(i + 3, len(lines))):
                next_line = lines[j].strip() if j < len(lines) else ""
                if next_line == "pass":
                    issues.append(Issue(
                        pattern_name="Swallowed Error",
                        severity=Severity.WARN,
                        line_number=i,
                        line_content=stripped,
                        description="Exception is caught and silently discarded. "
                                    "Errors will be invisible, making debugging extremely difficult.",
                        fix_hint="At minimum, log the error: except Exception as e: logger.error(f'Payment failed: {e}')",
                    ))
                    break
                elif next_line and not next_line.startswith("#"):
                    break

    return issues


def _check_missing_timeout(lines: list[str], language: str) -> list[Issue]:
    """Detect HTTP requests without timeout parameter."""
    issues = []
    request_pattern = re.compile(
        r'requests\.(get|post|put|delete|patch|head|options)\s*\('
    )

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if request_pattern.search(stripped):
            # Check this line and a few following lines for timeout=
            context = "\n".join(lines[i-1:min(i+4, len(lines))])
            if "timeout" not in context.lower():
                issues.append(Issue(
                    pattern_name="Missing Timeout",
                    severity=Severity.WARN,
                    line_number=i,
                    line_content=stripped,
                    description="HTTP request has no timeout. If the server hangs, "
                                "your application will hang indefinitely.",
                    fix_hint="Add timeout parameter: requests.get(url, timeout=10)",
                ))

    return issues


def _check_magic_numbers(lines: list[str], language: str) -> list[Issue]:
    """Detect unexplained magic numbers."""
    issues = []
    # Match standalone integers in expressions, not in common safe contexts
    magic_pattern = re.compile(r'(?<!["\'\w.])\b(\d+)\b(?!["\'\w.])')
    # Numbers that are generally acceptable (HTTP codes, powers of 2, ports)
    safe_numbers = {
        0, 1, 2, 10,
        100, 200, 201, 204, 301, 302, 304,
        400, 401, 403, 404, 405, 408, 409, 422, 429,
        500, 502, 503, 504,
        8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536,
        80, 443, 3000, 5000, 8000, 8080, 8443, 9000,
    }
    # Skip lines that are comments, imports, constants (ALL_CAPS =), or obvious config
    skip_line = re.compile(
        r'^\s*(?:#|//|\*|import|from|const\s+[A-Z_]+|[A-Z_]+\s*=|port|version|__version__)',
        re.IGNORECASE,
    )

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if skip_line.match(stripped):
            continue
        for match in magic_pattern.finditer(stripped):
            num = int(match.group(1))
            if num not in safe_numbers and num > 2:
                # Avoid flagging array indices, range(), common patterns
                context = stripped.lower()
                if any(ctx in context for ctx in [
                    "range(", "[::", "index", "len(", ".port", "sleep(",
                    "status_code", "status", "exit(", "sys.exit", "listen(",
                    ".listen", "timeout", "max_retries", "max_length",
                    "maxlength", "size", "width", "height", "margin",
                    "padding", "offset", "limit", "max_tokens",
                    "tokens", "chunk", "batch", "page", "per_page",
                    "capacity", "buffer", "workers", "threads",
                ]):
                    continue
                issues.append(Issue(
                    pattern_name="Magic Number",
                    severity=Severity.WARN,
                    line_number=i,
                    line_content=stripped,
                    description=f"The number {num} appears without explanation. "
                                "Magic numbers make code hard to understand and maintain.",
                    fix_hint=f"Extract to a named constant: SOME_CONSTANT = {num}  (use a descriptive name)",
                ))
                break  # One magic number issue per line

    return issues


def _check_select_star(lines: list[str], language: str) -> list[Issue]:
    """Detect SELECT * FROM queries."""
    issues = []
    pattern = re.compile(r'SELECT\s+\*\s+FROM', re.IGNORECASE)

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if pattern.search(stripped):
            issues.append(Issue(
                pattern_name="Inefficient Query",
                severity=Severity.WARN,
                line_number=i,
                line_content=stripped,
                description="SELECT * fetches all columns, including ones you don't need. "
                            "This wastes bandwidth and can cause performance issues at scale.",
                fix_hint="Specify only the columns you need: SELECT id, name, email FROM users",
            ))

    return issues


# --- INFO patterns (Python-specific) ---

def _check_missing_type_hints(lines: list[str], language: str) -> list[Issue]:
    """Detect Python functions without type hints."""
    if language != "python":
        return []

    issues = []
    func_pattern = re.compile(r'^\s*def\s+(\w+)\s*\((.*?)\)')

    for i, line in enumerate(lines, 1):
        match = func_pattern.match(line)
        if match:
            func_name = match.group(1)
            params = match.group(2)
            has_return_hint = "->" in line

            # Skip dunder methods and self/cls only functions
            if func_name.startswith("__") and func_name.endswith("__"):
                continue

            # Check if params have type hints (look for : in params, excluding default values)
            params_clean = params.replace("self", "").replace("cls", "").strip(", ")
            if params_clean and ":" not in params_clean:
                issues.append(Issue(
                    pattern_name="Missing Type Hints",
                    severity=Severity.INFO,
                    line_number=i,
                    line_content=line.strip(),
                    description=f"Function '{func_name}' has no type hints on parameters. "
                                "Type hints improve readability and enable better IDE support.",
                    fix_hint=f"Add type hints: def {func_name}(param: str) -> ReturnType:",
                ))
            elif not has_return_hint:
                issues.append(Issue(
                    pattern_name="Missing Type Hints",
                    severity=Severity.INFO,
                    line_number=i,
                    line_content=line.strip(),
                    description=f"Function '{func_name}' has no return type hint.",
                    fix_hint=f"Add return type: def {func_name}(...) -> ReturnType:",
                ))

    return issues


def _check_long_functions(lines: list[str], language: str) -> list[Issue]:
    """Detect functions longer than 50 lines."""
    issues = []

    if language == "python":
        func_starts = []
        func_pattern = re.compile(r'^(\s*)def\s+(\w+)\s*\(')
        for i, line in enumerate(lines, 1):
            match = func_pattern.match(line)
            if match:
                indent = len(match.group(1))
                func_starts.append((i, match.group(2), indent))

        for idx, (start_line, func_name, indent) in enumerate(func_starts):
            if idx + 1 < len(func_starts):
                end_line = func_starts[idx + 1][0] - 1
            else:
                end_line = len(lines)

            length = end_line - start_line + 1
            if length > 50:
                issues.append(Issue(
                    pattern_name="Long Function",
                    severity=Severity.INFO,
                    line_number=start_line,
                    line_content=lines[start_line - 1].strip(),
                    description=f"Function '{func_name}' is {length} lines long. "
                                "Long functions are harder to test and understand.",
                    fix_hint="Consider breaking it into smaller, focused functions.",
                ))
    elif language in ("javascript", "typescript"):
        func_pattern = re.compile(r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\(|function))')
        brace_count = 0
        current_func = None
        current_start = None

        for i, line in enumerate(lines, 1):
            match = func_pattern.search(line)
            if match and brace_count == 0:
                current_func = match.group(1) or match.group(2)
                current_start = i
                brace_count = line.count("{") - line.count("}")
            elif current_func:
                brace_count += line.count("{") - line.count("}")
                if brace_count <= 0:
                    length = i - current_start + 1
                    if length > 50:
                        issues.append(Issue(
                            pattern_name="Long Function",
                            severity=Severity.INFO,
                            line_number=current_start,
                            line_content=lines[current_start - 1].strip(),
                            description=f"Function '{current_func}' is {length} lines long.",
                            fix_hint="Consider breaking it into smaller, focused functions.",
                        ))
                    current_func = None
                    brace_count = 0

    return issues


def _check_missing_docstrings(lines: list[str], language: str) -> list[Issue]:
    """Detect Python public functions without docstrings."""
    if language != "python":
        return []

    issues = []
    func_pattern = re.compile(r'^\s*def\s+(\w+)\s*\(')

    for i, line in enumerate(lines, 1):
        match = func_pattern.match(line)
        if match:
            func_name = match.group(1)
            if func_name.startswith("_"):
                continue

            # Check next 2 non-empty lines for docstring
            has_docstring = False
            for j in range(i, min(i + 3, len(lines))):
                next_line = lines[j].strip() if j < len(lines) else ""
                if '"""' in next_line or "'''" in next_line:
                    has_docstring = True
                    break
                if next_line and not next_line.endswith("):") and not next_line.endswith(","):
                    break

            if not has_docstring:
                issues.append(Issue(
                    pattern_name="Missing Docstring",
                    severity=Severity.INFO,
                    line_number=i,
                    line_content=line.strip(),
                    description=f"Public function '{func_name}' has no docstring. "
                                "Docstrings help other developers understand the function's purpose.",
                    fix_hint=f'Add a docstring: def {func_name}(...):\n    """Brief description of what this function does."""',
                ))

    return issues


# --- CRITICAL: XSS Detection ---

def _check_xss(lines: list[str], language: str) -> list[Issue]:
    """Detect potential XSS vulnerabilities (innerHTML, dangerouslySetInnerHTML, document.write)."""
    if language not in ("javascript", "typescript"):
        return []

    issues = []
    patterns = [
        (re.compile(r'\.innerHTML\s*='), "innerHTML assignment"),
        (re.compile(r'dangerouslySetInnerHTML'), "dangerouslySetInnerHTML"),
        (re.compile(r'document\.write\s*\('), "document.write()"),
    ]

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        for pattern, desc in patterns:
            if pattern.search(stripped):
                issues.append(Issue(
                    pattern_name="XSS Vulnerability",
                    severity=Severity.CRITICAL,
                    line_number=i,
                    line_content=stripped,
                    description=f"Using {desc} can allow Cross-Site Scripting (XSS) attacks. "
                                "User input rendered as HTML lets attackers inject malicious scripts.",
                    fix_hint="Use textContent instead of innerHTML, or sanitize with DOMPurify: "
                             "DOMPurify.sanitize(userInput)  [CWE-79 / OWASP A03:2021]",
                ))
                break

    return issues


# --- CRITICAL: Path Traversal ---

def _check_path_traversal(lines: list[str], language: str) -> list[Issue]:
    """Detect potential path traversal vulnerabilities."""
    issues = []

    if language == "python":
        # open() or Path() with user-influenced variables and no validation
        patterns = [
            re.compile(r'open\s*\(\s*(?:request\.|params\.|args\.|f["\']|.*\+)'),
            re.compile(r'(?:send_file|send_from_directory)\s*\(\s*(?:request\.|params\.|f["\'])'),
        ]
    elif language in ("javascript", "typescript"):
        patterns = [
            re.compile(r'(?:readFile|readFileSync|createReadStream)\s*\(\s*(?:req\.|params\.|`)', re.IGNORECASE),
            re.compile(r'(?:res\.sendFile|res\.download)\s*\(\s*(?:req\.|params\.|`)', re.IGNORECASE),
        ]
    else:
        return []

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//"):
            continue
        for pattern in patterns:
            if pattern.search(stripped):
                issues.append(Issue(
                    pattern_name="Path Traversal",
                    severity=Severity.CRITICAL,
                    line_number=i,
                    line_content=stripped,
                    description="User input used in file path without sanitization. "
                                "An attacker can use '../' sequences to read arbitrary files on the server.",
                    fix_hint="Validate and sanitize paths: use os.path.realpath() and verify "
                             "the resolved path starts with your expected base directory.  [CWE-22 / OWASP A01:2021]",
                ))
                break

    return issues


# --- CRITICAL: Insecure Deserialization ---

def _check_insecure_deserialization(lines: list[str], language: str) -> list[Issue]:
    """Detect insecure deserialization (pickle.loads, yaml.load without Loader)."""
    issues = []

    if language == "python":
        patterns = [
            (re.compile(r'pickle\.loads?\s*\('), "pickle.load()",
             "Use json.loads() for data exchange, or hmac-sign pickled data if pickle is required."),
            (re.compile(r'yaml\.load\s*\([^)]*\)(?!.*Loader)'), "yaml.load() without SafeLoader",
             "Use yaml.safe_load() instead of yaml.load() to prevent arbitrary code execution."),
            (re.compile(r'marshal\.loads?\s*\('), "marshal.load()",
             "marshal is not safe for untrusted data. Use json or msgpack instead."),
        ]
    else:
        return []

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        for pattern, desc, fix in patterns:
            if pattern.search(stripped):
                issues.append(Issue(
                    pattern_name="Insecure Deserialization",
                    severity=Severity.CRITICAL,
                    line_number=i,
                    line_content=stripped,
                    description=f"Using {desc} with untrusted data allows arbitrary code execution. "
                                "An attacker can craft malicious payloads to take over the server.",
                    fix_hint=fix + "  [CWE-502 / OWASP A08:2021]",
                ))
                break

    return issues


# --- WARN: SSRF Detection ---

def _check_ssrf(lines: list[str], language: str) -> list[Issue]:
    """Detect potential Server-Side Request Forgery (SSRF)."""
    issues = []

    if language == "python":
        pattern = re.compile(
            r'requests\.\w+\s*\(\s*(?:f["\']|.*\+\s*|.*\.format\(|request\.|params\.|args\.)',
        )
    elif language in ("javascript", "typescript"):
        pattern = re.compile(
            r'(?:fetch|axios\.\w+|http\.get)\s*\(\s*(?:`.*\$\{|req\.|params\.|.*\+)',
        )
    else:
        return []

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//"):
            continue
        if pattern.search(stripped):
            issues.append(Issue(
                pattern_name="SSRF",
                severity=Severity.WARN,
                line_number=i,
                line_content=stripped,
                description="User input used directly in server-side HTTP request URL. "
                            "An attacker could make your server request internal services or cloud metadata endpoints.",
                fix_hint="Validate URLs against an allowlist of trusted domains. "
                         "Block private IP ranges (10.x, 172.16.x, 192.168.x, 169.254.169.254).  [CWE-918 / OWASP A10:2021]",
            ))

    return issues


# ---------------------------------------------------------------------------
# AI-Generated Code Pattern Detection
# Patterns statistically over-represented in AI-generated code.
# These are what Claude, Copilot, and ChatGPT frequently get wrong.
# ---------------------------------------------------------------------------

def _check_ai_mutable_default_args(lines: list[str], language: str) -> list[Issue]:
    """Detect mutable default arguments — top AI coding mistake."""
    if language != "python":
        return []
    issues = []
    pattern = re.compile(
        r'def\s+\w+\s*\(.*?(\w+\s*=\s*(?:\[\]|\{\}|set\(\)|list\(\)|dict\(\))).*?\)'
    )
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        m = pattern.search(stripped)
        if m:
            issues.append(Issue(
                pattern_name="Mutable Default Argument",
                severity=Severity.CRITICAL,
                line_number=i,
                line_content=stripped,
                description=(
                    f"Mutable default '{m.group(1)}' is shared across ALL calls to this function. "
                    "This is the #1 AI coding mistake — it creates hidden, persistent state that "
                    "accumulates between calls and causes impossible-to-debug behavior."
                ),
                fix_hint="Use None as sentinel: def foo(items=None): if items is None: items = []",
                is_ai_pattern=True,
            ))
    return issues


def _check_ai_wildcard_imports(lines: list[str], language: str) -> list[Issue]:
    """Detect wildcard imports — AI avoids specifying exact imports."""
    issues = []
    pattern = re.compile(r'^from\s+\S+\s+import\s+\*')
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if pattern.match(stripped):
            module = stripped.split()[1] if len(stripped.split()) > 1 else "module"
            issues.append(Issue(
                pattern_name="Wildcard Import",
                severity=Severity.WARN,
                line_number=i,
                line_content=stripped,
                description=(
                    f"'from {module} import *' pollutes the namespace and makes it impossible "
                    "to trace where names come from. AI models use wildcards to avoid "
                    "thinking about which specific names they need."
                ),
                fix_hint=f"Import explicitly: from {module} import ClassA, function_b",
                is_ai_pattern=True,
            ))
    return issues


def _check_ai_placeholder_logic(lines: list[str], language: str) -> list[Issue]:
    """Detect unimplemented placeholders — AI scaffolds but doesn't implement."""
    issues = []
    todo_pattern = re.compile(r'#\s*TODO\b', re.IGNORECASE)
    not_impl_pattern = re.compile(r'^\s*raise\s+NotImplementedError')
    fixme_pattern = re.compile(r'#\s*FIXME\b', re.IGNORECASE)

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if todo_pattern.search(stripped):
            issues.append(Issue(
                pattern_name="Placeholder Logic",
                severity=Severity.INFO,
                line_number=i,
                line_content=stripped,
                description=(
                    "TODO comment indicates functionality not yet implemented. "
                    "Review before merging to a production branch."
                ),
                fix_hint="Implement the required logic or track this as a ticket before releasing to production.",
                is_ai_pattern=True,
            ))
        elif fixme_pattern.search(stripped):
            issues.append(Issue(
                pattern_name="Placeholder Logic",
                severity=Severity.INFO,
                line_number=i,
                line_content=stripped,
                description="FIXME comment indicates a known issue that has not been resolved.",
                fix_hint="Fix the issue or document the reason it is deferred with a ticket reference.",
                is_ai_pattern=True,
            ))
        elif not_impl_pattern.match(stripped):
            issues.append(Issue(
                pattern_name="Unimplemented Method",
                severity=Severity.WARN,
                line_number=i,
                line_content=stripped,
                description=(
                    "Function raises NotImplementedError — this is scaffolding that has not been "
                    "filled in. Calling this path in production will raise an exception immediately."
                ),
                fix_hint="Implement the function body, or clearly document it as an abstract interface.",
                is_ai_pattern=True,
            ))
    return issues


def _check_ai_assert_for_validation(lines: list[str], language: str) -> list[Issue]:
    """Detect assert used for production input validation — fails silently with -O flag."""
    if language != "python":
        return []
    # Skip test files
    full_text = "\n".join(lines[:30])
    if any(x in full_text for x in ["import pytest", "import unittest", "from unittest"]):
        return []

    issues = []
    assert_pattern = re.compile(r'^\s*assert\s+')
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if assert_pattern.match(stripped):
            issues.append(Issue(
                pattern_name="Assert for Validation",
                severity=Severity.INFO,
                line_number=i,
                line_content=stripped,
                description=(
                    "assert is disabled when Python runs with the -O (optimize) flag, "
                    "silently skipping all checks. Consider replacing with explicit validation "
                    "for code paths that handle external input."
                ),
                fix_hint="For external input validation: if not condition: raise ValueError('Expected X, got Y')",
                is_ai_pattern=True,
            ))
    return issues


def _check_ai_os_system(lines: list[str], language: str) -> list[Issue]:
    """Detect os.system() — shell injection risk, classic AI shortcut."""
    if language != "python":
        return []
    issues = []
    pattern = re.compile(r'\bos\.system\s*\(')
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if pattern.search(stripped):
            issues.append(Issue(
                pattern_name="Shell Injection Risk",
                severity=Severity.CRITICAL,
                line_number=i,
                line_content=stripped,
                description=(
                    "os.system() passes the command string directly to the shell. "
                    "If any part contains user input, this allows arbitrary command execution. "
                    "AI models use os.system() as the 'easy' way to run shell commands."
                ),
                fix_hint="Use subprocess.run(['cmd', 'arg'], capture_output=True, check=True) — never pass shell=True with user input.",
                is_ai_pattern=True,
            ))
    return issues


def _check_ai_sync_in_async(lines: list[str], language: str) -> list[Issue]:
    """Detect blocking calls inside async functions — blocks the entire event loop."""
    if language != "python":
        return []
    issues = []
    blocking_patterns = [
        (re.compile(r'\btime\.sleep\s*\('), "time.sleep()", "asyncio.sleep()"),
        (re.compile(r'\brequests\.(get|post|put|delete|patch)\s*\('), "requests.*()", "aiohttp or httpx"),
    ]
    in_async = False
    async_indent = -1

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped:
            continue
        indent = len(line) - len(line.lstrip())
        if re.match(r'\s*async\s+def\s+', line):
            in_async = True
            async_indent = indent
        elif in_async and indent <= async_indent and stripped and not stripped.startswith('#'):
            if not re.match(r'\s*(async\s+def|@)', line):
                in_async = False
        if in_async and indent > async_indent:
            for pat, sync_name, async_name in blocking_patterns:
                if pat.search(stripped) and 'await' not in stripped:
                    issues.append(Issue(
                        pattern_name="Blocking Call in Async",
                        severity=Severity.WARN,
                        line_number=i,
                        line_content=stripped,
                        description=(
                            f"{sync_name} blocks the entire async event loop — "
                            "all other coroutines freeze until this call returns. "
                            "This is a top-3 AI async mistake."
                        ),
                        fix_hint=f"Replace with the async equivalent: {async_name}",
                        is_ai_pattern=True,
                    ))
                    break
    return issues


def _check_ai_debug_prints(lines: list[str], language: str) -> list[Issue]:
    """Detect print() in files that already use logging — AI debugging leftovers."""
    if language != "python":
        return []
    full_text_top = "\n".join(lines[:40])
    has_logging = "import logging" in full_text_top or "from logging" in full_text_top
    if not has_logging:
        return []

    issues = []
    print_pattern = re.compile(r'^\s*print\s*\(')
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if print_pattern.match(stripped):
            issues.append(Issue(
                pattern_name="Debug Print Statement",
                severity=Severity.INFO,
                line_number=i,
                line_content=stripped,
                description=(
                    "print() used instead of the logging module already imported in this file. "
                    "AI models add print() for debugging and forget to convert them. "
                    "print() has no log levels, no timestamps, and can't be disabled in production."
                ),
                fix_hint="Replace with: logging.debug('message') or logging.info('message')",
                is_ai_pattern=True,
            ))
    return issues


def _check_ai_missing_await(lines: list[str], language: str) -> list[Issue]:
    """Detect async library calls without await inside async functions."""
    if language != "python":
        return []
    issues = []
    needs_await = re.compile(
        r'\b(?:asyncio\.sleep|asyncio\.gather|asyncio\.wait|asyncio\.create_task|'
        r'session\.(?:get|post|put|delete|patch|request)|'
        r'aiohttp\.[\w.]+|asyncpg\.[\w.]+|aiomysql\.[\w.]+|'
        r'aiofiles\.open)\s*\(',
    )
    in_async = False
    async_indent = -1

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped:
            continue
        indent = len(line) - len(line.lstrip())
        if re.match(r'\s*async\s+def\s+', line):
            in_async = True
            async_indent = indent
        elif in_async and indent <= async_indent and stripped and not stripped.startswith('#'):
            if not re.match(r'\s*(async\s+def|@)', line):
                in_async = False
        if in_async and indent > async_indent:
            if needs_await.search(stripped) and 'await' not in stripped and not stripped.startswith('#'):
                issues.append(Issue(
                    pattern_name="Missing Await",
                    severity=Severity.CRITICAL,
                    line_number=i,
                    line_content=stripped,
                    description=(
                        "Async coroutine called without 'await'. The coroutine object is created "
                        "but never executed — this is completely silent and returns None or a "
                        "coroutine object instead of the actual result. Top AI async mistake."
                    ),
                    fix_hint="Add 'await' before the call. Example: result = await session.get(url)",
                    is_ai_pattern=True,
                ))
    return issues


# ---------------------------------------------------------------------------
# Concept extraction
# ---------------------------------------------------------------------------

# Maps pattern names to concepts they teach
CONCEPT_MAP = {
    "SQL Injection": ["Parameterized Queries", "SQL Injection Prevention"],
    "Hardcoded Credentials": ["Secrets Management", "Environment Variables"],
    "Code Injection": ["Input Validation", "Secure Evaluation"],
    "Race Condition": ["Mutex / Synchronization", "Goroutine Safety"],
    "Auth Middleware Order": ["Middleware Execution Order", "Express.js Security"],
    "Swallowed Error": ["Error Handling", "Exception Propagation"],
    "Missing Timeout": ["HTTP Timeout Management", "Resilient Network Calls"],
    "Magic Number": ["Named Constants", "Code Readability"],
    "Inefficient Query": ["Query Optimization", "Database Performance"],
    "Missing Type Hints": ["Type Annotations"],
    "Long Function": ["Function Decomposition", "Single Responsibility"],
    "Missing Docstring": ["Code Documentation"],
    "XSS Vulnerability": ["Output Encoding", "Cross-Site Scripting Prevention"],
    "Path Traversal": ["Input Sanitization", "Secure File Access"],
    "Insecure Deserialization": ["Safe Deserialization", "Input Validation"],
    "SSRF": ["URL Validation", "Server-Side Request Forgery Prevention"],
    "Mutable Default Argument": ["Python Default Arguments", "Function State Management"],
    "Wildcard Import": ["Python Import System", "Namespace Management"],
    "Placeholder Logic": ["Production Readiness", "Code Completeness"],
    "Unimplemented Method": ["Abstract Interfaces", "Production Readiness"],
    "Assert for Validation": ["Input Validation", "Python Optimization Flags"],
    "Shell Injection Risk": ["Command Injection", "subprocess vs os.system"],
    "Blocking Call in Async": ["Async/Await Patterns", "Event Loop Blocking"],
    "Debug Print Statement": ["Logging Best Practices", "Production Readiness"],
    "Missing Await": ["Async/Await Patterns", "Coroutine Execution"],
}

# Additional concept patterns detected from code (not issues)
CODE_CONCEPT_PATTERNS = {
    "Decorator Pattern": re.compile(r'@\w+'),
    "Context Manager": re.compile(r'\bwith\s+'),
    "List Comprehension": re.compile(r'\[.*\bfor\b.*\bin\b.*\]'),
    "Generator": re.compile(r'\byield\b'),
    "Async/Await": re.compile(r'\basync\b|\bawait\b'),
    "Regular Expressions": re.compile(r'\bre\.\w+\('),
    "Class Inheritance": re.compile(r'class\s+\w+\s*\((?!object\)|Exception\))'),
    "Lambda Functions": re.compile(r'\blambda\b'),
    "Recursion": None,  # Detected separately
}


def _extract_concepts(lines: list[str], issues: list[Issue], language: str) -> list[str]:
    """Extract educational concepts from code issues and patterns."""
    concepts = set()

    # Add concepts from detected issues
    for issue in issues:
        if issue.pattern_name in CONCEPT_MAP:
            for concept in CONCEPT_MAP[issue.pattern_name]:
                concepts.add(concept)

    # Add concepts from code patterns
    full_text = "\n".join(lines)
    for concept_name, pattern in CODE_CONCEPT_PATTERNS.items():
        if pattern and pattern.search(full_text):
            concepts.add(concept_name)

    return sorted(concepts)


# ---------------------------------------------------------------------------
# Main detection entry point
# ---------------------------------------------------------------------------

# All detection functions
ALL_CHECKS = [
    # CRITICAL
    _check_sql_injection,
    _check_hardcoded_credentials,
    _check_code_injection,
    _check_race_condition_go,
    _check_middleware_order,
    _check_xss,
    _check_path_traversal,
    _check_insecure_deserialization,
    # WARN
    _check_swallowed_errors,
    _check_missing_timeout,
    _check_magic_numbers,
    _check_select_star,
    _check_ssrf,
    # INFO
    _check_missing_type_hints,
    _check_long_functions,
    _check_missing_docstrings,
]

# AI-Generated Code Pattern checks
AI_PATTERN_CHECKS = [
    _check_ai_mutable_default_args,
    _check_ai_missing_await,
    _check_ai_os_system,
    _check_ai_wildcard_imports,
    _check_ai_placeholder_logic,
    _check_ai_assert_for_validation,
    _check_ai_sync_in_async,
    _check_ai_debug_prints,
    # Also include key security checks — AI commonly misses these too
    _check_hardcoded_credentials,
    _check_swallowed_errors,
]


def detect(filepath: str, custom_content: str | None = None, line_filter: set[int] | None = None) -> DetectionResult:
    """Run all rule-based detection patterns against a file.

    Args:
        filepath: Path to the source code file to analyze.
        custom_content: Raw string content (used for staged git scanning).
        line_filter: Set of line numbers to restrict issues to (used for git diff).

    Returns:
        DetectionResult with all detected issues and concepts.
    """
    path = Path(filepath)
    language = detect_language(filepath)

    if custom_content is not None:
        content = custom_content
    else:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="latin-1")

    lines = content.splitlines()

    # Run all checks
    all_issues: list[Issue] = []
    for check_fn in ALL_CHECKS:
        try:
            issues = check_fn(lines, language)
            all_issues.extend(issues)
        except Exception as e:
            logger.debug("Check %s failed: %s", check_fn.__name__, e)

    # Filter by line numbers if provided
    if line_filter is not None:
        all_issues = [i for i in all_issues if i.line_number in line_filter]

    # Filter out ignored lines (vibecheck-disable)
    filtered_issues = []
    for i in all_issues:
        content = i.line_content.lower()
        if "vibecheck-disable" in content:
            continue
        # Also check the line above if it exists
        if i.line_number > 1:
            prev_line = lines[i.line_number - 2].lower()
            if "vibecheck-disable" in prev_line:
                continue
        filtered_issues.append(i)
    all_issues = filtered_issues

    # Extract concepts
    concepts = _extract_concepts(lines, all_issues, language)

    return DetectionResult(
        filepath=filepath,
        language=language,
        issues=all_issues,
        concepts=concepts,
    )


def detect_fast(filepath: str) -> DetectionResult:
    """Fast detection for pre-commit hook — CRITICAL and WARN only, no INFO.

    Skips expensive checks to stay under 2-second budget.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    language = detect_language(filepath)
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = path.read_text(encoding="latin-1")

    lines = content.splitlines()

    # Only run CRITICAL and WARN checks
    fast_checks = [
        _check_sql_injection,
        _check_hardcoded_credentials,
        _check_code_injection,
        _check_race_condition_go,
        _check_middleware_order,
        _check_xss,
        _check_path_traversal,
        _check_insecure_deserialization,
        _check_swallowed_errors,
        _check_missing_timeout,
        _check_select_star,
        _check_ssrf,
        _check_ai_mutable_default_args,
        _check_ai_missing_await,
        _check_ai_os_system,
    ]

    all_issues: list[Issue] = []
    for check_fn in fast_checks:
        try:
            issues = check_fn(lines, language)
            all_issues.extend(issues)
        except Exception as e:
            logger.debug("Fast check %s failed: %s", check_fn.__name__, e)

    return DetectionResult(
        filepath=filepath,
        language=language,
        issues=all_issues,
        concepts=[],
    )


def detect_ai_patterns(filepath: str, custom_content: str | None = None) -> AIAuditResult:
    """Scan a file specifically for AI-generated code anti-patterns.

    Returns an AIAuditResult with only AI-pattern-tagged issues and a
    confidence score indicating how likely the code is AI-generated.
    """
    path = Path(filepath)
    language = detect_language(filepath)

    if custom_content is not None:
        content = custom_content
    else:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="latin-1")

    lines = content.splitlines()

    all_issues: list[Issue] = []
    for check_fn in AI_PATTERN_CHECKS:
        try:
            found = check_fn(lines, language)
            # Ensure all issues from AI checks are tagged
            for issue in found:
                issue.is_ai_pattern = True
            all_issues.extend(found)
        except Exception as e:
            logger.debug("AI check %s failed: %s", check_fn.__name__, e)

    # De-duplicate by line number + pattern name
    seen = set()
    deduped = []
    for issue in all_issues:
        key = (issue.line_number, issue.pattern_name)
        if key not in seen:
            seen.add(key)
            deduped.append(issue)

    return AIAuditResult(
        filepath=filepath,
        language=language,
        ai_issues=deduped,
    )
