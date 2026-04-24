"""Rule-based pattern detection for code issues.

This module handles ALL issue detection. LLM is never used for detection —
only for explanation after issues are found.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from vibecheck.core.severity import Severity


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


@dataclass
class DetectionResult:
    """Complete detection result for a file."""

    filepath: str
    language: str
    issues: list[Issue] = field(default_factory=list)
    concepts: list[str] = field(default_factory=list)


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
                fix_hint='Use parameterized queries: cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))',
            ))
        elif format_sql.search(stripped):
            issues.append(Issue(
                pattern_name="SQL Injection",
                severity=Severity.CRITICAL,
                line_number=i,
                line_content=stripped,
                description="User input interpolated into SQL via .format(). "
                            "An attacker can inject arbitrary SQL commands.",
                fix_hint='Use parameterized queries: cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))',
            ))
        elif concat_sql.search(stripped):
            issues.append(Issue(
                pattern_name="SQL Injection",
                severity=Severity.CRITICAL,
                line_number=i,
                line_content=stripped,
                description="User input concatenated into SQL string. "
                            "An attacker can inject arbitrary SQL commands.",
                fix_hint='Use parameterized queries: cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))',
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
                            "These will be visible in version control history.",
                fix_hint="Use environment variables: os.environ.get('API_KEY') or a secrets manager.",
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
                fix_hint="Use ast.literal_eval() for safe evaluation, or restructure to avoid eval entirely.",
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
                             "DOMPurify.sanitize(userInput)",
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
                             "the resolved path starts with your expected base directory.",
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
                    fix_hint=fix,
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
                         "Block private IP ranges (10.x, 172.16.x, 192.168.x, 169.254.169.254).",
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


def detect(filepath: str) -> DetectionResult:
    """Run all rule-based detection patterns against a file.

    Args:
        filepath: Path to the source code file to analyze.

    Returns:
        DetectionResult with all detected issues and concepts.
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

    # Run all checks
    all_issues: list[Issue] = []
    for check_fn in ALL_CHECKS:
        try:
            issues = check_fn(lines, language)
            all_issues.extend(issues)
        except Exception:
            # Don't let one failing check break everything
            pass

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
    ]

    all_issues: list[Issue] = []
    for check_fn in fast_checks:
        try:
            issues = check_fn(lines, language)
            all_issues.extend(issues)
        except Exception:
            pass

    return DetectionResult(
        filepath=filepath,
        language=language,
        issues=all_issues,
        concepts=[],
    )
