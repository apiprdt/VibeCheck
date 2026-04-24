"""Tests for vibecheck's rule-based detector.

Run with: pytest tests/ -v
"""

import pytest
from vibecheck.core.detector import (
    detect, detect_fast, detect_language, Issue, DetectionResult,
    _check_sql_injection, _check_hardcoded_credentials, _check_code_injection,
    _check_race_condition_go, _check_middleware_order, _check_swallowed_errors,
    _check_missing_timeout, _check_magic_numbers, _check_select_star,
    _check_missing_type_hints, _check_long_functions, _check_missing_docstrings,
    _check_xss, _check_path_traversal, _check_insecure_deserialization, _check_ssrf,
)
from vibecheck.core.severity import Severity


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

class TestLanguageDetection:
    def test_python(self):
        assert detect_language("app.py") == "python"

    def test_javascript(self):
        assert detect_language("index.js") == "javascript"

    def test_typescript(self):
        assert detect_language("app.ts") == "typescript"

    def test_go(self):
        assert detect_language("main.go") == "go"

    def test_jsx(self):
        assert detect_language("Component.jsx") == "javascript"

    def test_tsx(self):
        assert detect_language("Component.tsx") == "typescript"

    def test_unknown(self):
        assert detect_language("README.md") == "unknown"


# ---------------------------------------------------------------------------
# CRITICAL patterns
# ---------------------------------------------------------------------------

class TestSQLInjection:
    def test_fstring_sql(self):
        lines = ['cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")']
        issues = _check_sql_injection(lines, "python")
        assert len(issues) >= 1
        assert issues[0].severity == Severity.CRITICAL
        assert "SQL Injection" in issues[0].pattern_name

    def test_format_sql(self):
        lines = ['"SELECT * FROM users WHERE id = {}".format(user_id)']
        issues = _check_sql_injection(lines, "python")
        assert len(issues) >= 1

    def test_concat_sql(self):
        lines = ['"SELECT * FROM users WHERE id = " + user_id']
        issues = _check_sql_injection(lines, "python")
        assert len(issues) >= 1

    def test_parameterized_safe(self):
        lines = ['cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))']
        issues = _check_sql_injection(lines, "python")
        assert len(issues) == 0

    def test_multiline_execute_fstring(self):
        lines = [
            'cursor.execute(',
            '    f"SELECT * FROM users WHERE id = {user_id}"',
            ')',
        ]
        issues = _check_sql_injection(lines, "python")
        assert len(issues) >= 1


class TestHardcodedCredentials:
    def test_api_key(self):
        lines = ['API_KEY = "sk-1234567890abcdef"']
        issues = _check_hardcoded_credentials(lines, "python")
        assert len(issues) == 1
        assert issues[0].severity == Severity.CRITICAL

    def test_password(self):
        lines = ['password = "supersecret123"']
        issues = _check_hardcoded_credentials(lines, "python")
        assert len(issues) == 1

    def test_env_var_safe(self):
        lines = ['API_KEY = os.environ.get("API_KEY")']
        issues = _check_hardcoded_credentials(lines, "python")
        assert len(issues) == 0

    def test_placeholder_excluded(self):
        lines = ['api_key = "your-api-key-here"']
        issues = _check_hardcoded_credentials(lines, "python")
        assert len(issues) == 0

    def test_comment_excluded(self):
        lines = ['# password = "should_be_ignored"']
        issues = _check_hardcoded_credentials(lines, "python")
        assert len(issues) == 0


class TestCodeInjection:
    def test_eval_dynamic(self):
        lines = ['result = eval(user_input)']
        issues = _check_code_injection(lines, "python")
        assert len(issues) == 1
        assert issues[0].severity == Severity.CRITICAL

    def test_eval_literal_safe(self):
        lines = ['result = eval("2 + 2")']
        issues = _check_code_injection(lines, "python")
        assert len(issues) == 0


class TestRaceCondition:
    def test_goroutine_no_mutex(self):
        lines = [
            'package main',
            '',
            'var counter int',
            '',
            'func increment() {',
            '    go func() {',
            '        counter++',
            '    }()',
            '}',
        ]
        issues = _check_race_condition_go(lines, "go")
        assert len(issues) == 1
        assert issues[0].severity == Severity.CRITICAL

    def test_with_mutex_safe(self):
        lines = [
            'var counter int',
            'var mu sync.Mutex',
            'func increment() {',
            '    go func() {',
            '        mu.Lock()',
            '        counter++',
            '        mu.Unlock()',
            '    }()',
            '}',
        ]
        issues = _check_race_condition_go(lines, "go")
        assert len(issues) == 0

    def test_non_go_skipped(self):
        lines = ['var counter = 0']
        issues = _check_race_condition_go(lines, "python")
        assert len(issues) == 0


class TestMiddlewareOrder:
    def test_route_before_auth(self):
        lines = [
            'const app = express()',
            "app.get('/profile', (req, res) => {",
            '  res.json(req.user)',
            '})',
            'app.use(authMiddleware)',
        ]
        issues = _check_middleware_order(lines, "javascript")
        assert len(issues) == 1
        assert issues[0].severity == Severity.CRITICAL

    def test_auth_before_route_safe(self):
        lines = [
            'const app = express()',
            'app.use(authMiddleware)',
            "app.get('/profile', (req, res) => {",
            '  res.json(req.user)',
            '})',
        ]
        issues = _check_middleware_order(lines, "javascript")
        assert len(issues) == 0

    def test_non_js_skipped(self):
        lines = ['app.get("/test")']
        issues = _check_middleware_order(lines, "python")
        assert len(issues) == 0


class TestXSS:
    def test_innerhtml(self):
        lines = ['element.innerHTML = userInput']
        issues = _check_xss(lines, "javascript")
        assert len(issues) == 1
        assert issues[0].severity == Severity.CRITICAL

    def test_dangerously_set(self):
        lines = ['<div dangerouslySetInnerHTML={{__html: data}} />']
        issues = _check_xss(lines, "javascript")
        assert len(issues) == 1

    def test_document_write(self):
        lines = ['document.write(userInput)']
        issues = _check_xss(lines, "javascript")
        assert len(issues) == 1

    def test_textcontent_safe(self):
        lines = ['element.textContent = userInput']
        issues = _check_xss(lines, "javascript")
        assert len(issues) == 0

    def test_non_js_skipped(self):
        lines = ['element.innerHTML = test']
        issues = _check_xss(lines, "python")
        assert len(issues) == 0


class TestPathTraversal:
    def test_python_open_fstring(self):
        lines = ["open(f'/uploads/{filename}')"]
        issues = _check_path_traversal(lines, "python")
        assert len(issues) == 1
        assert issues[0].severity == Severity.CRITICAL

    def test_js_readfile_req(self):
        lines = ["fs.readFileSync(req.params.path)"]
        issues = _check_path_traversal(lines, "javascript")
        assert len(issues) == 1


class TestInsecureDeserialization:
    def test_pickle_loads(self):
        lines = ['data = pickle.loads(user_data)']
        issues = _check_insecure_deserialization(lines, "python")
        assert len(issues) == 1
        assert issues[0].severity == Severity.CRITICAL

    def test_yaml_load_unsafe(self):
        lines = ['config = yaml.load(content)']
        issues = _check_insecure_deserialization(lines, "python")
        assert len(issues) == 1

    def test_yaml_safe_load_ok(self):
        lines = ['config = yaml.safe_load(content)']
        issues = _check_insecure_deserialization(lines, "python")
        assert len(issues) == 0

    def test_non_python_skipped(self):
        lines = ['pickle.loads(data)']
        issues = _check_insecure_deserialization(lines, "javascript")
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# WARN patterns
# ---------------------------------------------------------------------------

class TestSwallowedErrors:
    def test_except_pass(self):
        lines = [
            'try:',
            '    do_something()',
            'except Exception as e:',
            '    pass',
        ]
        issues = _check_swallowed_errors(lines, "python")
        assert len(issues) == 1
        assert issues[0].severity == Severity.WARN

    def test_except_with_logging_safe(self):
        lines = [
            'try:',
            '    do_something()',
            'except Exception as e:',
            '    logger.error(e)',
        ]
        issues = _check_swallowed_errors(lines, "python")
        assert len(issues) == 0


class TestMissingTimeout:
    def test_requests_no_timeout(self):
        lines = ['response = requests.get("https://example.com")']
        issues = _check_missing_timeout(lines, "python")
        assert len(issues) == 1
        assert issues[0].severity == Severity.WARN

    def test_requests_with_timeout_safe(self):
        lines = ['response = requests.get("https://example.com", timeout=10)']
        issues = _check_missing_timeout(lines, "python")
        assert len(issues) == 0


class TestMagicNumbers:
    def test_unexplained_number(self):
        lines = ['    if attempts > 37:']
        issues = _check_magic_numbers(lines, "python")
        assert len(issues) == 1
        assert issues[0].severity == Severity.WARN

    def test_http_status_safe(self):
        lines = ['}, { status: 503 });']
        issues = _check_magic_numbers(lines, "javascript")
        assert len(issues) == 0

    def test_power_of_2_safe(self):
        lines = ['max_tokens: isImage ? 2048 : 4096,']
        issues = _check_magic_numbers(lines, "javascript")
        assert len(issues) == 0

    def test_port_3000_safe(self):
        lines = ['app.listen(3000)']
        issues = _check_magic_numbers(lines, "javascript")
        assert len(issues) == 0

    def test_constant_definition_safe(self):
        lines = ['MAX_RETRIES = 5']
        issues = _check_magic_numbers(lines, "python")
        assert len(issues) == 0

    def test_comment_safe(self):
        lines = ['# retry 3 times']
        issues = _check_magic_numbers(lines, "python")
        assert len(issues) == 0

    def test_zero_one_two_safe(self):
        lines = ['x = 0', 'y = 1', 'z = 2']
        issues = _check_magic_numbers(lines, "python")
        assert len(issues) == 0


class TestSelectStar:
    def test_select_star(self):
        lines = ['cursor.execute("SELECT * FROM users")']
        issues = _check_select_star(lines, "python")
        assert len(issues) == 1

    def test_specific_columns_safe(self):
        lines = ['cursor.execute("SELECT id, name FROM users")']
        issues = _check_select_star(lines, "python")
        assert len(issues) == 0


class TestSSRF:
    def test_python_fstring_url(self):
        lines = ['response = requests.get(f"https://api.example.com/{user_input}")']
        issues = _check_ssrf(lines, "python")
        assert len(issues) == 1
        assert issues[0].severity == Severity.WARN

    def test_js_template_literal(self):
        lines = ['const resp = await fetch(`https://api.example.com/${userId}`)']
        issues = _check_ssrf(lines, "javascript")
        assert len(issues) == 1


# ---------------------------------------------------------------------------
# INFO patterns
# ---------------------------------------------------------------------------

class TestMissingTypeHints:
    def test_no_hints(self):
        lines = ['def get_user(user_id):']
        issues = _check_missing_type_hints(lines, "python")
        assert len(issues) == 1
        assert issues[0].severity == Severity.INFO

    def test_with_hints_safe(self):
        lines = ['def get_user(user_id: int) -> User:']
        issues = _check_missing_type_hints(lines, "python")
        assert len(issues) == 0

    def test_dunder_skipped(self):
        lines = ['def __init__(self):']
        issues = _check_missing_type_hints(lines, "python")
        assert len(issues) == 0

    def test_non_python_skipped(self):
        lines = ['def get_user(user_id):']
        issues = _check_missing_type_hints(lines, "javascript")
        assert len(issues) == 0


class TestMissingDocstrings:
    def test_public_no_docstring(self):
        lines = ['def get_user(user_id):', '    return db.get(user_id)']
        issues = _check_missing_docstrings(lines, "python")
        assert len(issues) == 1

    def test_with_docstring_safe(self):
        lines = ['def get_user(user_id):', '    """Get user by ID."""', '    return db.get(user_id)']
        issues = _check_missing_docstrings(lines, "python")
        assert len(issues) == 0

    def test_private_skipped(self):
        lines = ['def _internal(x):', '    return x']
        issues = _check_missing_docstrings(lines, "python")
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# Integration: detect() function
# ---------------------------------------------------------------------------

class TestDetectIntegration:
    def test_python_example(self):
        result = detect("examples/python_bad.py")
        assert result.language == "python"
        assert len(result.issues) > 0
        # Should find SQL injection and hardcoded credentials
        pattern_names = {i.pattern_name for i in result.issues}
        assert "SQL Injection" in pattern_names
        assert "Hardcoded Credentials" in pattern_names

    def test_node_example(self):
        result = detect("examples/node_bad.js")
        assert result.language == "javascript"
        pattern_names = {i.pattern_name for i in result.issues}
        assert "Auth Middleware Order" in pattern_names

    def test_go_example(self):
        result = detect("examples/go_bad.go")
        assert result.language == "go"
        pattern_names = {i.pattern_name for i in result.issues}
        assert "Race Condition" in pattern_names

    def test_detect_fast_no_info(self):
        result = detect_fast("examples/python_bad.py")
        # detect_fast should NOT include INFO severity
        info_issues = [i for i in result.issues if i.severity == Severity.INFO]
        assert len(info_issues) == 0

    def test_concepts_extracted(self):
        result = detect("examples/python_bad.py")
        assert len(result.concepts) > 0
        assert "SQL Injection Prevention" in result.concepts

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            detect("nonexistent_file.py")
