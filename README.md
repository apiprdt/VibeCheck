<p align="center">
  <img src="https://raw.githubusercontent.com/apiprdt/VibeCheck/main/assets/logo.jpg" alt="VibeCheck Logo" width="400">
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
  <a href="https://x.com/AfifErditaa"><img src="https://img.shields.io/badge/X%20(Twitter)-@AfifErditaa-black?logo=x&logoColor=white&labelColor=gray&style=for-the-badge" alt="Twitter"></a>
</p>

---

### **AI-Powered Code Auditing with a "Senior Developer" Vibe.**

VibeCheck is an interactive CLI tool designed to help developers understand, audit, and secure their codebase. It combines strict **rule-based scanning** (AST-based, no hallucinations) with advanced **AI explanations** to ensure you don't just fix bugs—you learn from them.

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

### 2. Run Your First Audit
```bash
vibecheck app.py --learn
```

---

## 🛠️ Advanced Usage (The "Pro" Vibe)

### 🩺 **Error Diagnosis Mode**
Stop guessing why your code crashed. Paste an error message or stack trace, and VibeCheck will analyze it within the context of your file.
```bash
vibecheck main.py --error "ValueError: invalid literal for int() with base 10"
```

### 📉 **Knowledge Debt Scan**
Identify "dark" parts of your repository that haven't been audited or contain hidden architectural risks.
```bash
vibecheck --debt ./src
```

### 👔 **Senior Perspective & Risk Analysis**
Get feedback on high-level architecture and production risks that static rules might miss.
```bash
vibecheck core/logic.py --senior --risks
```

### ⚓ **Git Integration**
Only scan files that are currently staged (ready to commit):
```bash
vibecheck --staged
```
Install a pre-commit hook that automatically blocks commits containing **Critical** issues:
```bash
vibecheck --install-hook --fail-on-critical
```

---

## ✨ Key Features

### 🛡️ **Rule-Based Engine & Local Guidelines**
VibeCheck uses a strict engine to catch SQL Injections, Hardcoded Credentials, and more. It also reads your **`.vibecheck_rules.md`** to enforce project-specific coding standards.

### 🧠 **Smart Global Caching**
VibeCheck caches every AI response locally (`~/.vibecheck/cache`). Subsequent scans of the same code are **instant and free**.

### 🎓 **Pedagogical AI (ELI5)**
Use **`--learn`** to get complex flaws explained through simple real-world analogies. Perfect for junior developers and students.

### 💬 **Interactive Terminal Chat**
Don't understand a fix? Launch **`--chat`** to have a direct conversation with the "Virtual Senior Developer" about your code.

---

## ⚙️ Configuration & Providers

VibeCheck is **universal**. Configure your favorite provider via environment variables or `~/.vibecheck/config.yaml`.

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
