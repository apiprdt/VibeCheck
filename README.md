# vibecheck

**Understand the code your AI wrote.**

AI tools make you faster. vibecheck makes sure you actually understand what you're shipping. It tracks which concepts you've learned so you depend less on AI over time.

---

## Install

```bash
pip install vibecheck
```

Or install from source:

```bash
git clone https://github.com/apiprdt/vibecheck.git
cd vibecheck
pip install -e .
```

## Setup

Set your API key for AI-powered explanations:

```bash
# OpenAI (default)
export OPENAI_API_KEY=sk-...

# Or Anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# Or use a local model via Ollama (fully offline)
export OLLAMA_API_BASE=http://localhost:11434
export VIBECHECK_MODEL=ollama/llama3
```

> **vibecheck works without an API key.** Rule-based detection runs locally and catches real issues instantly. The API key enables AI-powered explanations and concept teaching.

---

## Usage

### Analyze a file

```bash
vibecheck src/auth/login.py
```

```
────────── vibecheck -- src/auth/login.py ──────────

┌─ 🚨 CRITICAL ─────────────────────────────────────┐
│                                                    │
│  SQL Injection -- line 7                           │
│    f"SELECT * FROM users WHERE id = {user_id}"     │
│    User input interpolated directly into SQL.      │
│    Fix: cursor.execute(                            │
│      "SELECT * FROM users WHERE id = ?",           │
│      (user_id,)                                    │
│    )                                               │
│                                                    │
│  Hardcoded Credentials -- line 21                  │
│    API_KEY = "sk-1234567890abcdef"                 │
│    Fix: os.environ.get('API_KEY')                  │
│                                                    │
└────────────────────────────────────────────────────┘

┌─ 📖 WHAT THIS CODE DOES ──────────────────────────┐
│                                                    │
│  This file handles user lookup from a SQLite       │
│  database and processes payments via Stripe.       │
│                                                    │
└────────────────────────────────────────────────────┘

┌─ ⚠️ WARNINGS ─────────────────────────────────────┐
│                                                    │
│  Swallowed Error -- line 16                        │
│    except Exception as e: pass                     │
│    Fix: logger.error(f'Payment failed: {e}')       │
│                                                    │
└────────────────────────────────────────────────────┘

┌─ 🧠 CONCEPTS IN THIS FILE ────────────────────────┐
│                                                    │
│  ★ Parameterized Queries -- NEW                    │
│  ★ Error Handling -- NEW                           │
│  ★ Secrets Management -- NEW                      │
│                                                    │
└────────────────────────────────────────────────────┘
```

### Diagnose an error

```bash
vibecheck --error "NameError: name 'result' is not defined" src/payments.py
```

### Scan for knowledge debt

```bash
vibecheck --debt ./src
```

```
┌─ 📊 KNOWLEDGE GAP ────────────────────────────────┐
│  12 files total                                    │
│  4 files analyzed before                           │
│  8 files never analyzed                            │
└────────────────────────────────────────────────────┘

┌─ 🚨 START HERE (critical, needs review) ──────────┐
│  → src/auth/login.py                               │
│    contains: SQL Injection, Hardcoded Credentials  │
│  → src/payments/stripe.py                          │
│    contains: Swallowed Error                       │
└────────────────────────────────────────────────────┘
```

### Optional flags

```bash
vibecheck file.py --learn     # Deeper concept explanations with examples
vibecheck file.py --senior    # What a senior dev would change
vibecheck file.py --risks     # Extended risk analysis
```

---

## Commands

| Command | Description |
|---|---|
| `vibecheck <file>` | Analyze a file for issues and concepts |
| `vibecheck <file> --json` | Output results as JSON (for CI/CD) |
| `vibecheck --error "msg" <file>` | Diagnose an error in context |
| `vibecheck --debt <dir>` | Scan directory for knowledge debt |
| `vibecheck --install-hook` | Install git pre-commit hook |
| `vibecheck --reset-memory` | Clear all learned concepts |
| `vibecheck --version` | Show version |

---

## Why vibecheck?

Cursor, Claude Code, and Aider make you ship faster. **vibecheck makes sure you understand what you shipped.**

- **Rule-based detection** catches real issues instantly — no AI needed, no API key required
- **AI explanations** teach you *why* it matters and *how* to fix it
- **Concept memory** tracks what you've learned, so explanations get shorter over time
- **Pre-commit hook** catches issues before they hit your repo

vibecheck isn't a linter. It's a mentor that remembers what you know.

---

## How It Works

1. **Detection** — Pure rule-based regex patterns catch CRITICAL, WARN, and INFO issues. No AI involved. Fast and deterministic.
2. **Explanation** — If an API key is configured, detected issues and concepts are sent to the LLM for clear, educational explanations.
3. **Memory** — Concepts you've seen are tracked in a local SQLite database (`~/.vibecheck/knowledge.db`). The more you use vibecheck, the shorter the explanations get.

### Concept Learning Progression

| Times Seen | Display | Behavior |
|---|---|---|
| 0 (new) | `★ Concept -- NEW` | Full 3-5 sentence explanation |
| 1 | `→ Concept -- seen before` | One-line reminder |
| 2+ | `✓ Concept -- [LEARNED -- skipping]` | Skipped entirely |

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI API key | — |
| `ANTHROPIC_API_KEY` | Anthropic API key | — |
| `OLLAMA_API_BASE` | Ollama API URL | — |
| `VIBECHECK_MODEL` | LLM model to use | `gpt-4o-mini` |

### Config File (optional)

Create `~/.vibecheck/config.yaml`:

```yaml
# LLM model
model: gpt-4o-mini

# Severity filter: only show issues at this level or above
# severity_filter: warn

# Patterns to ignore
# ignore_patterns:
#   - Magic Number
#   - Missing Docstring

# Files to ignore (glob patterns)
# ignore_files:
#   - "*.test.js"
#   - "*.spec.ts"
#   - "test_*.py"
```

Priority: env var > config file > default.

---

## Local Model Support (Ollama)

Run completely offline with [Ollama](https://ollama.com):

```bash
# Install and pull a model
ollama pull llama3

# Configure vibecheck
export OLLAMA_API_BASE=http://localhost:11434
export VIBECHECK_MODEL=ollama/llama3

# Use normally
vibecheck src/app.py
```

---

## Pre-Commit Hook

```bash
# Install (warnings only, doesn't block commits)
vibecheck --install-hook

# Install (blocks commits on critical issues)
vibecheck --install-hook --fail-on-critical

# Override any time
git commit --no-verify
```

The hook uses rule-based detection only (no LLM calls) to stay under 2 seconds.

---

## What It Detects

### CRITICAL
- SQL Injection (f-string, .format(), concatenation in queries)
- Hardcoded Credentials (passwords, API keys, tokens, secrets)
- Code Injection (eval() with dynamic input)
- Race Conditions (Go: shared variable in goroutine without mutex)
- Auth Middleware Order (Express.js: routes before auth middleware)
- XSS Vulnerability (innerHTML, dangerouslySetInnerHTML, document.write)
- Path Traversal (user input in file paths without sanitization)
- Insecure Deserialization (pickle.loads, yaml.load without SafeLoader)

### WARN
- Swallowed Errors (except: pass)
- Missing Timeout (requests.get() without timeout)
- Magic Numbers (unexplained integers — HTTP codes and powers of 2 excluded)
- Inefficient Queries (SELECT *)
- SSRF (user input in server-side HTTP request URLs)

### INFO
- Missing Type Hints (Python)
- Long Functions (>50 lines)
- Missing Docstrings (public functions)

---

## Development

```bash
# Install in dev mode
pip install -e .
pip install pytest

# Run tests
pytest tests/ -v
```

82 tests covering all 16 detection patterns, memory progression, CLI commands, and JSON output.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

Key areas of interest:
- New detection patterns for more languages
- Improved concept extraction
- Better LLM prompt engineering
- Documentation and examples

---

## License

MIT — see [LICENSE](LICENSE).
