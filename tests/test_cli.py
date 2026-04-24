"""Tests for the CLI entry point."""

import subprocess
import sys
import json
import os


def _run_vibecheck(*args) -> subprocess.CompletedProcess:
    """Run vibecheck as a subprocess and return stdout."""
    # Force no color and utf-8 for consistent test results
    env = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "NO_COLOR": "1",
        "FORCE_COLOR": "0"
    }
    result = subprocess.run(
        [sys.executable, "-m", "vibecheck"] + list(args),
        capture_output=True,
        env=env,
        encoding="utf-8",
        errors="replace",
    )
    return result


class TestCLIBasic:
    def test_version(self):
        result = _run_vibecheck("--version")
        assert "vibecheck" in (result.stdout or "")
        assert "0.1.0" in (result.stdout or "")

    def test_help(self):
        result = _run_vibecheck("--help")
        stdout = result.stdout or ""
        assert "Analyze code files" in stdout
        assert "--error" in stdout
        assert "--debt" in stdout
        assert "--json" in stdout

    def test_file_not_found(self):
        result = _run_vibecheck("nonexistent_file.py")
        assert result.returncode != 0

    def test_no_args_shows_help(self):
        result = _run_vibecheck()
        stdout = result.stdout or ""
        assert "Usage:" in stdout or "vibecheck" in stdout


class TestCLIAnalysis:
    def test_python_analysis(self):
        result = _run_vibecheck("examples/python_bad.py")
        stdout = result.stdout or ""
        assert "SQL Injection" in stdout
        assert "Hardcoded Credentials" in stdout

    def test_node_analysis(self):
        result = _run_vibecheck("examples/node_bad.js")
        stdout = result.stdout or ""
        assert "Auth Middleware Order" in stdout

    def test_go_analysis(self):
        result = _run_vibecheck("examples/go_bad.go")
        stdout = result.stdout or ""
        assert "Race Condition" in stdout


class TestCLIJsonOutput:
    def test_json_output_valid(self):
        result = _run_vibecheck("examples/python_bad.py", "--json")
        stdout = (result.stdout or "").strip()
        data = json.loads(stdout)
        assert "filepath" in data
        assert "issues" in data
        assert "concepts" in data
        assert "summary" in data

    def test_json_has_issues(self):
        result = _run_vibecheck("examples/python_bad.py", "--json")
        stdout = (result.stdout or "").strip()
        data = json.loads(stdout)
        assert data["summary"]["critical"] > 0
        assert data["summary"]["total"] > 0

    def test_json_issue_structure(self):
        result = _run_vibecheck("examples/python_bad.py", "--json")
        stdout = (result.stdout or "").strip()
        data = json.loads(stdout)
        issue = data["issues"][0]
        assert "pattern" in issue
        assert "severity" in issue
        assert "line" in issue
        assert "description" in issue
        assert "fix" in issue


class TestCLIDebtScan:
    def test_debt_scan(self):
        result = _run_vibecheck("--debt", "examples")
        stdout = result.stdout or ""
        assert "KNOWLEDGE GAP" in stdout or "files total" in stdout
