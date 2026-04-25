"""Tests for AI-generated code pattern detection.

Each test uses synthetic code that mimics real AI-generated anti-patterns
to verify the detection engine catches them accurately with zero false negatives.
"""

import pytest
from vibecheck.core.detector import (
    detect_ai_patterns,
    AIAuditResult,
    _check_ai_mutable_default_args,
    _check_ai_wildcard_imports,
    _check_ai_placeholder_logic,
    _check_ai_assert_for_validation,
    _check_ai_os_system,
    _check_ai_sync_in_async,
    _check_ai_debug_prints,
    _check_ai_missing_await,
)
from vibecheck.core.severity import Severity


# ---------------------------------------------------------------------------
# Fixtures: synthetic AI-generated code snippets
# ---------------------------------------------------------------------------

MUTABLE_DEFAULT_CODE = [
    "def process_items(items=[]):",
    "    items.append('new')",
    "    return items",
]

MUTABLE_DEFAULT_DICT_CODE = [
    "def create_config(options={}):",
    "    options['key'] = 'value'",
    "    return options",
]

CLEAN_DEFAULT_CODE = [
    "def process_items(items=None):",
    "    if items is None:",
    "        items = []",
    "    items.append('new')",
    "    return items",
]

WILDCARD_IMPORT_CODE = [
    "from os import *",
    "from pathlib import Path",
    "from utils import *",
]

PLACEHOLDER_CODE = [
    "def handle_payment():",
    "    # TODO: implement payment logic",
    "    pass",
    "",
    "def validate_input():",
    "    # FIXME: this is broken",
    "    return True",
    "",
    "def abstract_method():",
    "    raise NotImplementedError",
]

ASSERT_VALIDATION_CODE = [
    "def process_order(user_id, amount):",
    "    assert user_id is not None",
    "    assert amount > 0",
    "    return True",
]

ASSERT_IN_TEST_CODE = [
    "import pytest",
    "",
    "def test_something():",
    "    assert 1 == 1",
]

OS_SYSTEM_CODE = [
    "import os",
    "def deploy():",
    "    os.system('rm -rf /tmp/build')",
    "    os.system(f'docker build -t {tag} .')",
]

SYNC_IN_ASYNC_CODE = [
    "import time",
    "import asyncio",
    "",
    "async def fetch_data():",
    "    time.sleep(5)",
    "    return 'data'",
]

SYNC_IN_ASYNC_REQUESTS_CODE = [
    "import requests",
    "import asyncio",
    "",
    "async def get_user():",
    "    response = requests.get('https://api.example.com/user')",
    "    return response.json()",
]

DEBUG_PRINTS_WITH_LOGGING = [
    "import logging",
    "",
    "logger = logging.getLogger(__name__)",
    "",
    "def process():",
    "    print('debug: starting process')",
    "    logger.info('Processing started')",
    "    print('done')",
]

DEBUG_PRINTS_WITHOUT_LOGGING = [
    "def process():",
    "    print('starting process')",
    "    print('done')",
]

MISSING_AWAIT_CODE = [
    "import asyncio",
    "",
    "async def main():",
    "    asyncio.sleep(1)",
    "    result = asyncio.gather(task1(), task2())",
    "    return result",
]

CORRECT_AWAIT_CODE = [
    "import asyncio",
    "",
    "async def main():",
    "    await asyncio.sleep(1)",
    "    result = await asyncio.gather(task1(), task2())",
    "    return result",
]

# A file that looks like real AI output — multiple patterns combined
AI_GENERATED_FILE = [
    "from utils import *",
    "import os",
    "import logging",
    "",
    "logger = logging.getLogger(__name__)",
    "",
    "def process_batch(items=[], config={}):",
    "    # TODO: add error handling",
    "    print('Starting batch')",
    "    assert len(items) > 0",
    "    os.system(f'process {items[0]}')",
    "    return items",
]


# ---------------------------------------------------------------------------
# Unit tests for individual checkers
# ---------------------------------------------------------------------------

class TestMutableDefaultArgs:
    def test_detects_list_default(self):
        issues = _check_ai_mutable_default_args(MUTABLE_DEFAULT_CODE, "python")
        assert len(issues) >= 1
        assert issues[0].severity == Severity.CRITICAL
        assert issues[0].is_ai_pattern is True
        assert "items=[]" in issues[0].line_content

    def test_detects_dict_default(self):
        issues = _check_ai_mutable_default_args(MUTABLE_DEFAULT_DICT_CODE, "python")
        assert len(issues) >= 1
        assert "options={}" in issues[0].line_content

    def test_clean_default_passes(self):
        issues = _check_ai_mutable_default_args(CLEAN_DEFAULT_CODE, "python")
        assert len(issues) == 0

    def test_skips_non_python(self):
        issues = _check_ai_mutable_default_args(MUTABLE_DEFAULT_CODE, "javascript")
        assert len(issues) == 0


class TestWildcardImports:
    def test_detects_wildcard(self):
        issues = _check_ai_wildcard_imports(WILDCARD_IMPORT_CODE, "python")
        assert len(issues) == 2  # os and utils
        assert all(i.is_ai_pattern for i in issues)

    def test_ignores_explicit_imports(self):
        issues = _check_ai_wildcard_imports(["from pathlib import Path"], "python")
        assert len(issues) == 0


class TestPlaceholderLogic:
    def test_detects_todo(self):
        issues = _check_ai_placeholder_logic(PLACEHOLDER_CODE, "python")
        todo_issues = [i for i in issues if "TODO" in i.line_content]
        assert len(todo_issues) >= 1
        assert todo_issues[0].severity == Severity.INFO

    def test_detects_fixme(self):
        issues = _check_ai_placeholder_logic(PLACEHOLDER_CODE, "python")
        fixme_issues = [i for i in issues if "FIXME" in i.line_content]
        assert len(fixme_issues) >= 1

    def test_detects_not_implemented(self):
        issues = _check_ai_placeholder_logic(PLACEHOLDER_CODE, "python")
        ni_issues = [i for i in issues if i.pattern_name == "Unimplemented Method"]
        assert len(ni_issues) >= 1
        assert ni_issues[0].severity == Severity.WARN


class TestAssertForValidation:
    def test_detects_assert_in_production_code(self):
        issues = _check_ai_assert_for_validation(ASSERT_VALIDATION_CODE, "python")
        assert len(issues) == 2
        assert all(i.severity == Severity.INFO for i in issues)

    def test_skips_test_files(self):
        issues = _check_ai_assert_for_validation(ASSERT_IN_TEST_CODE, "python")
        assert len(issues) == 0

    def test_skips_non_python(self):
        issues = _check_ai_assert_for_validation(ASSERT_VALIDATION_CODE, "go")
        assert len(issues) == 0


class TestOsSystem:
    def test_detects_os_system(self):
        issues = _check_ai_os_system(OS_SYSTEM_CODE, "python")
        assert len(issues) == 2
        assert all(i.severity == Severity.CRITICAL for i in issues)

    def test_skips_non_python(self):
        issues = _check_ai_os_system(OS_SYSTEM_CODE, "javascript")
        assert len(issues) == 0


class TestSyncInAsync:
    def test_detects_time_sleep_in_async(self):
        issues = _check_ai_sync_in_async(SYNC_IN_ASYNC_CODE, "python")
        assert len(issues) >= 1
        assert "time.sleep" in issues[0].line_content

    def test_detects_requests_in_async(self):
        issues = _check_ai_sync_in_async(SYNC_IN_ASYNC_REQUESTS_CODE, "python")
        assert len(issues) >= 1

    def test_skips_non_python(self):
        issues = _check_ai_sync_in_async(SYNC_IN_ASYNC_CODE, "go")
        assert len(issues) == 0


class TestDebugPrints:
    def test_detects_print_when_logging_exists(self):
        issues = _check_ai_debug_prints(DEBUG_PRINTS_WITH_LOGGING, "python")
        assert len(issues) == 2
        assert all(i.severity == Severity.INFO for i in issues)

    def test_ignores_print_without_logging(self):
        issues = _check_ai_debug_prints(DEBUG_PRINTS_WITHOUT_LOGGING, "python")
        assert len(issues) == 0


class TestMissingAwait:
    def test_detects_missing_await(self):
        issues = _check_ai_missing_await(MISSING_AWAIT_CODE, "python")
        assert len(issues) >= 1
        assert all(i.severity == Severity.CRITICAL for i in issues)

    def test_correct_await_passes(self):
        issues = _check_ai_missing_await(CORRECT_AWAIT_CODE, "python")
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# Integration tests for detect_ai_patterns()
# ---------------------------------------------------------------------------

class TestDetectAiPatterns:
    """Test the full detect_ai_patterns pipeline with a temp file."""

    def test_ai_generated_file_high_confidence(self, tmp_path):
        """A file with many AI patterns should return HIGH confidence."""
        f = tmp_path / "ai_code.py"
        f.write_text("\n".join(AI_GENERATED_FILE), encoding="utf-8")

        result = detect_ai_patterns(str(f))

        assert isinstance(result, AIAuditResult)
        assert result.ai_confidence == "HIGH"
        assert result.ai_pattern_count >= 4
        assert all(i.is_ai_pattern for i in result.ai_issues)

        # Verify specific patterns were caught
        pattern_names = {i.pattern_name for i in result.ai_issues}
        assert "Wildcard Import" in pattern_names
        assert "Mutable Default Argument" in pattern_names
        assert "Shell Injection Risk" in pattern_names

    def test_clean_file_returns_clean(self, tmp_path):
        """A well-written file should return CLEAN confidence."""
        clean_code = (
            "from pathlib import Path\n"
            "import logging\n\n"
            "logger = logging.getLogger(__name__)\n\n"
            "def process(items=None):\n"
            "    if items is None:\n"
            "        items = []\n"
            "    logger.info('Processing %d items', len(items))\n"
            "    return items\n"
        )
        f = tmp_path / "clean_code.py"
        f.write_text(clean_code, encoding="utf-8")

        result = detect_ai_patterns(str(f))
        assert result.ai_confidence == "CLEAN"
        assert result.ai_pattern_count == 0

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            detect_ai_patterns("/nonexistent/file.py")

    def test_deduplication(self, tmp_path):
        """Same issue on same line should not be reported twice."""
        code = "from os import *\n"
        f = tmp_path / "dupe.py"
        f.write_text(code, encoding="utf-8")

        result = detect_ai_patterns(str(f))
        line1_issues = [i for i in result.ai_issues if i.line_number == 1]
        pattern_names = [i.pattern_name for i in line1_issues]
        # No duplicate pattern names on same line
        assert len(pattern_names) == len(set(pattern_names))

    def test_non_python_returns_limited_results(self, tmp_path):
        """Non-Python files should still return a result (not crash)."""
        f = tmp_path / "app.js"
        f.write_text("const x = 1;\n// TODO: fix this\n", encoding="utf-8")

        result = detect_ai_patterns(str(f))
        assert isinstance(result, AIAuditResult)
        # Should still catch TODO via placeholder logic
        assert result.language == "javascript"


class TestAIAuditResultProperties:
    """Test the AIAuditResult dataclass properties."""

    def test_confidence_levels(self):
        from vibecheck.core.detector import Issue

        def make_result(n_issues):
            issues = [
                Issue(
                    pattern_name=f"Pattern{i}",
                    severity=Severity.WARN,
                    line_number=i,
                    line_content=f"line {i}",
                    description="desc",
                    fix_hint="fix",
                    is_ai_pattern=True,
                )
                for i in range(n_issues)
            ]
            return AIAuditResult(filepath="test.py", language="python", ai_issues=issues)

        assert make_result(0).ai_confidence == "CLEAN"
        assert make_result(1).ai_confidence == "LOW"
        assert make_result(2).ai_confidence == "MEDIUM"
        assert make_result(3).ai_confidence == "MEDIUM"
        assert make_result(4).ai_confidence == "HIGH"
        assert make_result(10).ai_confidence == "HIGH"

    def test_pattern_count(self):
        result = AIAuditResult(filepath="test.py", language="python", ai_issues=[])
        assert result.ai_pattern_count == 0
