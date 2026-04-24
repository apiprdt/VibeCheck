# Contributing to vibecheck

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/apiprdt/vibecheck.git
cd vibecheck

# Install in dev mode
pip install -e .

# Verify it works
vibecheck examples/python_bad.py
```

## Areas of Interest

- **New detection patterns** — Add rule-based checks for more languages or more issue types
- **Better concept extraction** — Improve how we identify what concepts are used in code
- **LLM prompt tuning** — Better explanations, more concise teaching
- **Documentation** — More examples, better guides
- **Tests** — We need more automated tests

## Adding a Detection Pattern

1. Open `vibecheck/core/detector.py`
2. Create a new function following this pattern:

```python
def _check_your_pattern(lines: list[str], language: str) -> list[Issue]:
    """Detect [description of what you're checking]."""
    issues = []
    # Your detection logic here
    for i, line in enumerate(lines, 1):
        if your_condition:
            issues.append(Issue(
                pattern_name="Your Pattern Name",
                severity=Severity.WARN,  # or CRITICAL or INFO
                line_number=i,
                line_content=line.strip(),
                description="Clear explanation of the issue.",
                fix_hint="Actionable fix with code example.",
            ))
    return issues
```

3. Add it to `ALL_CHECKS` list at the bottom of the file
4. Add concept mappings in `CONCEPT_MAP` if relevant
5. Test with an example file

## Code Style

- Use type hints on all function signatures
- Add docstrings to all public functions
- Keep detection functions pure — they take `(lines, language)` and return `list[Issue]`
- Never use LLM for detection — only for explanation

## Commit Messages

Use clear, descriptive commit messages:
- `feat: add XSS detection pattern for JavaScript`
- `fix: reduce false positives in magic number check`
- `docs: add Ollama setup guide`

## Pull Requests

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Test with all example files
5. Submit PR with clear description

## Questions?

Open an issue — we're happy to help.
