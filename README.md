# 🛡️ VibeCheck v1.1.0 (Beta)
**The AI Code Safety Firewall for the Agentic Era.**

In April 2026, we’re shipping code 10x faster using agents, but we’re inheriting 100x more **"Hallucination Debt"**. VibeCheck is a professional CLI tool designed to audit, secure, and explain AI-generated code with 100% structural precision.

![VibeCheck Audit](https://via.placeholder.com/800x400/000000/FFFFFF?text=VibeCheck+Senior+Developer+Audit)

---

## 🔥 Key Features

### 1. 🚨 AI Hallucination Detector (`--ai-audit`)
Specifically targets "fake correctness" patterns that Claude, GPT-5, and Copilot often miss.
- **Silent Agent Traps:** Detects `except: pass` blocks used by agents to hide failures.
- **AI Overconfidence:** Flags nested data access without safety checks.
- **Mutable Default Hallucinations:** Caught with 100% precision via AST.

### 2. 🧠 AST Structural Analysis
Unlike generic linters, VibeCheck uses **Abstract Syntax Tree (AST)** analysis for Python. It understands the *structure* of your code, not just the text. It's immune to comments, spaces, or formatting tricks.

### 3. 👨‍💻 Virtual Senior Developer (`--senior`)
Get a high-level perspective on architectural flaws, not just syntax errors. VibeCheck explains *why* a pattern is dangerous using ELI5 analogies.

### 4. 🛡️ The Git Gatekeeper SOP (`--install-hook`)
Make security mandatory. Install a pre-commit hook that blocks commits containing critical AI bugs.
```bash
vibecheck --install-hook --fail-on-critical
```

### 5. 🎨 Custom Themes & Syntax Highlighting
Personalize your audit experience. Supports custom border colors and syntax highlighting for code snippets via `config.yaml`.

---

## 🚀 Quick Start

### Installation
```bash
# Clone the repo
git clone https://github.com/youruser/vibecheck.git
cd vibecheck

# Setup environment
python -m venv .venv
source .venv/bin/activate  # Or .\.venv\Scripts\activate on Windows
pip install -e .
```

### Basic Usage
```bash
# 1. Initialize your project
vibecheck --init

# 2. Run a standard audit
vibecheck path/to/file.py

# 3. Run a deep AI Hallucination scan
vibecheck path/to/file.py --ai-audit

# 4. Get senior dev advice + learn concepts
vibecheck path/to/file.py --senior --learn

# 5. Start an interactive session to fix issues
vibecheck path/to/file.py --chat
```

---

## 🛠️ Configuration & SOP

### Local Rules (`.vibecheck_rules.md`)
Define team-specific standards. VibeCheck reads this file and applies your custom rules to every scan.

### Custom Theme (`.vibecheck/config.yaml`)
```yaml
theme:
  critical_border: "magenta"
  warning_border: "orange1"
  info_border: "cyan"
```

### The "Zero-Debt" Protocol
Scan your entire project to identify never-before-analyzed files:
```bash
vibecheck --debt .
```

---

## 💎 Why VibeCheck?

AI optimizes for code that **looks** correct. VibeCheck ensures it **is** correct.
- **Deterministic:** Same code, same result. No AI "mood swings" during detection.
- **Educational:** Every fix comes with a lesson, turning junior devs into seniors.
- **Agent-Ready:** Built specifically to be the safety layer for autonomous coding agents.

**Built by a 16-year-old developer in 24h to prove that AI tools should focus on integrity, not just speed.** 🛡️🚀
