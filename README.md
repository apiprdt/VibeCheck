<p align="center">
  <img src="https://raw.githubusercontent.com/apiprdt/VibeCheck/main/assets/logo.jpg" alt="VibeCheck Logo" width="400">
</p>

<h2 align="center">Catch what Claude misses. Deterministic AI code safety — in your terminal.</h2>

<p align="center">
  <a href="https://pypi.org/project/vibecheck-ai-tool/"><img src="https://img.shields.io/pypi/v/vibecheck-ai-tool?color=black&labelColor=gray&style=for-the-badge" alt="PyPI"></a>
  <a href="https://pypi.org/project/vibecheck-ai-tool/"><img src="https://img.shields.io/pypi/pyversions/vibecheck-ai-tool?color=black&labelColor=gray&style=for-the-badge" alt="Python Versions"></a>
  <a href="https://github.com/apiprdt/vibecheck/blob/main/LICENSE"><img src="https://img.shields.io/github/license/apiprdt/vibecheck?color=black&labelColor=gray&style=for-the-badge" alt="License"></a>
</p>

<p align="center">
  <a href="https://github.com/apiprdt/vibecheck"><img src="https://img.shields.io/badge/PRs-Welcome-black?labelColor=gray&style=for-the-badge" alt="PRs Welcome"></a>
  <a href="https://github.com/apiprdt/vibecheck"><img src="https://img.shields.io/github/stars/apiprdt/vibecheck?color=black&labelColor=gray&style=for-the-badge" alt="Stars"></a>
  <a href="https://x.com/AfifErditaa"><img src="https://img.shields.io/badge/X%20(Twitter)-@AfifErditaa-black?logo=x&logoColor=white&labelColor=gray&style=for-the-badge" alt="Twitter"></a>
</p>

---

### **The AI Code Safety Firewall for the Agentic Era (April 2026)**

VibeCheck is a deterministic CLI security auditing tool built to mitigate the "AI Hallucination Debt" of 2025-2026. It catches the patterns **Claude, Copilot, and GPT-5 consistently get wrong**. It combines a strict rule-based engine (no hallucinations, same result every time) with AI-powered explanations to ensure you don't just find bugs — you understand and fix them.

---

## 🎬 Cinematic Walkthrough

<table align="center">
  <tr>
    <td align="center"><b>1. Project-Specific Rules</b><br/><img src="https://raw.githubusercontent.com/apiprdt/VibeCheck/main/assets/vibe1.png" width="400"></td>
    <td align="center"><b>2. Security Audit</b><br/><img src="https://raw.githubusercontent.com/apiprdt/VibeCheck/main/assets/vibe2.png" width="400"></td>
  </tr>
  <tr>
    <td align="center"><b>3. Educational Analogies (ELI5)</b><br/><img src="https://raw.githubusercontent.com/apiprdt/VibeCheck/main/assets/vibe3.png" width="400"></td>
    <td align="center"><b>4. Security Deep-Dive</b><br/><img src="https://raw.githubusercontent.com/apiprdt/VibeCheck/main/assets/vibe4.png" width="400"></td>
  </tr>
  <tr>
    <td align="center"><b>5. Concept Memory Tracking</b><br/><img src="https://raw.githubusercontent.com/apiprdt/VibeCheck/main/assets/vibe5.png" width="400"></td>
    <td align="center"><b>6. AI Fix Suggestions</b><br/><img src="https://raw.githubusercontent.com/apiprdt/VibeCheck/main/assets/vibe6.png" width="400"></td>
  </tr>
</table>

---

## 🚀 Quick Start

### 1. Installation
```bash
pip install vibecheck-ai-tool
```

### 2. Initialization (Optional but Recommended)
Set up your `.vibecheck_rules.md` and check API keys in one go:
```bash
vibecheck --init
```

### 3. Basic Audit
Scan any file and get AI-powered explanations:
```bash
vibecheck app.py
```

---

## 💡 Core Modes

VibeCheck adapts to how you want to work:

*   **`--learn`**: (ELI5 Mode) Uses real-world analogies to explain complex security concepts.
*   **`--chat`** or **`-c`**: Starts an interactive chat session with the "Senior Dev" about the file.
*   **`--fast`**: Skip the AI and run only the rule-based engine (Instant & Free).
*   **`--ai-audit`** or **`-a`**: Scan specifically for AI-generated code anti-patterns.

```bash
# Audit a file for AI-generated anti-patterns
vibecheck app.py --ai-audit

# Learn & Chat at the same time
vibecheck app.py --learn --chat
```

---

## 🛠️ Pro Features (Senior Dev Tools)

### 🤖 **AI Audit (New)**
Outputs an **AI Confidence Score** (CLEAN → LOW → MEDIUM → HIGH) with a breakdown of every anti-pattern found.

#### **The Signature Hallucination Pack:**
*   **AST Structural Engine:** Uses Abstract Syntax Tree analysis for Python (100% precision, immune to formatting tricks).
*   **Silent Agent Traps:** Detects `except: pass` blocks used by agents to hide failures.
*   **AI Overconfidence:** Flags complex nested data access without safety checks.

### 🩺 **Error Diagnosis**
Paste a crash message to diagnose it within your code context.
```bash
vibecheck main.py --error "IndexError: list index out of range"
```

### 📉 **Knowledge Debt Scan**
Scan your repo to see which files haven't been audited or have critical issues.
```bash
vibecheck --debt ./src
```

### 👔 **Senior & Risk Review**
Get high-level architectural feedback and production risk analysis.
```bash
vibecheck logic.py --senior --risks
```

---

## ⚓ Automation & CI/CD

### **Git Integration**
Scan only staged files before you commit:
```bash
vibecheck --staged
```
Install a pre-commit hook:
```bash
vibecheck --install-hook --fail-on-critical
```

### **CI/CD Support**
Output results as JSON for easy integration with other tools:
```bash
vibecheck app.py --json
```

### 🎨 **Custom Themes**
Personalize your audit experience via `config.yaml` or `.vibecheck/config.yaml`:
```yaml
theme:
  critical_border: "magenta"
  warning_border: "orange1"
  info_border: "cyan"
```

---

## ✨ Key Features

### 🛡️ **Rule-Based Engine & Local Guidelines**
VibeCheck uses a strict engine to catch SQL Injections, Hardcoded Credentials, and more—with **CWE and OWASP references** for every critical security vulnerability. It reads your **`.vibecheck_rules.md`** to enforce project-specific standards.

### 🧠 **Smart Global Caching**
VibeCheck caches every AI response locally (`~/.vibecheck/cache`). Subsequent scans of the same code are **instant and free**.

### 🧹 **Memory Management**
VibeCheck remembers what you've learned. To start fresh:
```bash
vibecheck --reset-memory
```

---

## 🆚 Why VibeCheck vs. Just Asking Claude?

Claude, Copilot, and ChatGPT optimize for code that **looks** correct. They don't simulate execution order, run your code, or enforce your team's rules. VibeCheck does.

| Capability | VibeCheck | Claude / ChatGPT |
| :--- | :---: | :---: |
| **AST Structural Analysis** (No Hallucinations) | ✅ | ❌ |
| Deterministic (same code = same result) | ✅ | ❌ |
| Enforces your team's custom rules | ✅ | ❌ |
| Remembers what you've already learned | ✅ | ❌ |
| Git pre-commit integration | ✅ | ❌ |
| Scans entire directories for debt | ✅ | ❌ |
| Detects auth middleware order bugs | ✅ | ❌ (rarely) |
| CI/CD JSON output | ✅ | ❌ |
| Free to run (rule-based mode) | ✅ | ❌ |

---

## ⚙️ Configuration & Providers

VibeCheck supports multiple programming languages (Python, JavaScript, TypeScript, Go) and is **model-agnostic**. Configure your favorite provider via environment variables or `~/.vibecheck/config.yaml`.

| Provider | Environment Variable | Default Model |
| :--- | :--- | :--- |
| **Groq** (Fastest) | `GROQ_API_KEY` | `llama-3.3-70b` |
| **OpenAI** | `OPENAI_API_KEY` | `gpt-4o-mini` |
| **Anthropic** | `ANTHROPIC_API_KEY` | `claude-3.5-sonnet` |
| **Google** | `GOOGLE_API_KEY` | `gemini-1.5-pro` |
| **Ollama** | `VIBECHECK_ENTERPRISE_MODE=1` | `ollama/llama3` |

---

## 👨‍💻 Developed by a 16-Year-Old Creator
Created in 24 hours to prove that AI tools should focus on **education**, not just automation. Architected & Maintained by [Afif Erdita](https://github.com/apiprdt).

---

## 📄 License
MIT License.
