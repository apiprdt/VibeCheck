<p align="center">
  <img src="assets/logo.png" alt="VibeCheck Logo" width="400">
</p>

<h2 align="center">"VibeCheck: The Virtual Senior Developer in Your Terminal"</h2>

<p align="center">
  <a href="https://pypi.org/project/vibecheck-ai-tool/"><img src="https://img.shields.io/pypi/v/vibecheck-ai-tool?color=black&labelColor=gray&style=for-the-badge" alt="PyPI"></a>
  <a href="https://pypi.org/project/vibecheck-ai-tool/"><img src="https://img.shields.io/pypi/pyversions/vibecheck-ai-tool?color=black&labelColor=gray&style=for-the-badge" alt="Python Versions"></a>
  <a href="https://github.com/apiprdt/vibecheck/blob/main/LICENSE"><img src="https://img.shields.io/github/license/apiprdt/vibecheck?color=black&labelColor=gray&style=for-the-badge" alt="License"></a>
</p>
<p align="center">
  <a href="https://github.com/apiprdt/vibecheck"><img src="https://img.shields.io/badge/PRs-Welcome-black?labelColor=gray&style=for-the-badge" alt="PRs Welcome"></a>
  <a href="https://github.com/apiprdt/vibecheck"><img src="https://img.shields.io/github/stars/apiprdt/vibecheck?color=black&labelColor=gray&style=for-the-badge" alt="Stars"></a>
  <a href="https://x.com/apiprdt"><img src="https://img.shields.io/badge/Twitter-Follow-black?logo=x&logoColor=white&labelColor=gray&style=for-the-badge" alt="Twitter"></a>
</p>

---

**Understand the code your AI wrote.**

AI tools make you faster. vibecheck makes sure you actually understand what you're shipping. It acts as an interactive tutor and a strict code auditor directly in your terminal, tracking what you've learned so you depend less on AI over time.

---

## Install

```bash
pip install vibecheck-ai-tool
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

# Or Google Gemini
export GOOGLE_API_KEY=your-key
export VIBECHECK_MODEL=gemini/gemini-1.5-flash

# Or Mistral
export MISTRAL_API_KEY=your-key
export VIBECHECK_MODEL=mistral/mistral-large-latest

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

### Git Integration (The "Senior Dev" Workflow)

Scan only files that are currently staged for commit. It reads directly from the git stage, ignoring uncommitted working tree changes, and filters issues to only lines that were actually modified:

```bash
# Scan staged files with full AI explanation
vibecheck --staged

# Scan staged files locally (NO AI, lightning fast — perfect for hooks)
vibecheck --staged --fast
```

### Optional flags

```bash
vibecheck file.py --learn     # Absolute Beginner Mode (ELI5 analogies & examples)
vibecheck file.py --chat      # Interactive AI Tutor REPL session after scanning
vibecheck file.py --senior    # What a senior dev would change
vibecheck file.py --risks     # Extended risk analysis
vibecheck file.py --json      # Output results as JSON
```

---

## The "Zero-Friction" Workflow

### 1. Inline Ignore (Suppress False Positives)
Senior Devs hate noise. If VibeCheck flags a safe line, silence it forever by adding `# vibecheck-disable` (Python) or `// vibecheck-disable` (JS) to the line or the line directly above it.

```python
# vibecheck-disable
LIMIT = 14  # This magic number is intended and will be ignored by VibeCheck
```

### 2. Interactive Tutor (`--chat`)
If the explanation isn't clear, start an interactive session.
```bash
vibecheck src/app.py --learn --chat
```
VibeCheck will open a `Prompt` in your terminal where you can ask follow-up questions like *"Wait, what does the recipe represent in that analogy?"*

---

## Project-Specific Rules (Continuous Learning)

vibecheck learns your team's specific coding guidelines over time. 
Create a `.vibecheck_rules.md` file anywhere in your project:

```markdown
# VibeCheck Project Guidelines
## Python
1. ALWAYS use SQLAlchemy ORM, never raw SQL.
2. Use `structlog` for logging, never `print()`.
```

vibecheck will automatically inject these rules as context, acting like a Virtual Senior Developer that enforces your specific project culture.

**Monorepo Support:** VibeCheck searches hierarchically. If you have different `.vibecheck_rules.md` files in `frontend/` and `backend/`, it will combine them up to 5 levels deep.

---

## Commands

| Command | Description |
|---|---|
| `vibecheck <file>` | Analyze a file for issues and concepts |
| `vibecheck <file> --chat` | Start interactive chat session after scan |
| `vibecheck --staged` | Analyze only files staged for commit |
| `vibecheck --staged --fast`| Analyze staged files with local rules only (No AI) |
| `vibecheck <file> --json` | Output results as JSON (for CI/CD) |
| `vibecheck --error "msg" <file>` | Diagnose an error in context |
| `vibecheck --debt <dir>` | Scan directory for knowledge debt |
| `vibecheck --install-hook` | Install git pre-commit hook |
| `vibecheck --reset-memory` | Clear all learned concepts |
| `vibecheck --version` | Show version |

---

## Why vibecheck?

Cursor, Claude Code, and Aider make you ship faster. **vibecheck makes sure you understand what you shipped.**

- **Rule-based detection** catches real issues instantly — no AI needed, no API key required.
- **Smart Caching** makes repeated scans of the same file instantaneous.
- **AI explanations** teach you *why* it matters and *how* to fix it.
- **Concept memory** tracks what you've learned, so explanations get shorter over time.
- **Project Context** learns your team's specific rules via `.vibecheck_rules.md`.
- **Git integration** (`--staged`) eliminates noise by only auditing what you're about to ship.

vibecheck isn't a linter. It's a Virtual Senior Developer that remembers what you know and protects your codebase.

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
| `GOOGLE_API_KEY` | Google AI (Gemini) key | — |
| `OLLAMA_API_BASE` | Ollama API URL | — |
| `VIBECHECK_MODEL` | LLM model to use (LiteLLM format) | `gpt-4o-mini` |
| `VIBECHECK_ENTERPRISE_MODE` | Set to `1` to block Cloud APIs (Forces Ollama) | `0` |

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

## Local Model Support (Ollama & Enterprise Security)

Run completely offline with [Ollama](https://ollama.com):

```bash
# Install and pull a model
ollama pull llama3

# Configure vibecheck
export OLLAMA_API_BASE=http://localhost:11434
export VIBECHECK_MODEL=ollama/llama3
```

**Enterprise Security Mode**
For organizations with strict Data Loss Prevention (DLP) policies, you can forcefully block all cloud LLM providers:

```bash
export VIBECHECK_ENTERPRISE_MODE=1
```
When this is active, VibeCheck will completely ignore `OPENAI_API_KEY` and refuse to run unless an Ollama local model is provided.

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
