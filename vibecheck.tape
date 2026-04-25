# vibecheck.tape
# Professional Demo Scenario for VibeCheck v1.0.0

# --- Setup Aesthetics ---
Output assets/demo.gif
Set FontSize 22
Set Width 1200
Set Height 650
Set Theme "Catppuccin Macchiato"
Set WindowBar Colorful
Set TypingSpeed 60ms
Set Padding 20
Set Shell powershell

# --- Intro ---
Hide
Type "vibecheck --version"
Enter
Sleep 500ms
Show
Type "# 🚀 Launching VibeCheck v1.0.0"
Sleep 1s
Enter

# --- Scenario 1: ELI5 Mode (For Absolute Beginners) ---
Type "# 1. Teaching Absolute Beginners with Analogies"
Sleep 500ms
Enter
Type "vibecheck examples/python_bad.py --learn"
Sleep 500ms
Enter
Sleep 5s

# --- Scenario 2: Project Guidelines ---
Type "# 2. Enforcing Local Project Rules"
Sleep 500ms
Enter
Type "vibecheck examples/python_bad.py"
Sleep 500ms
Enter
Sleep 3s

# --- Scenario 3: Git Staged (Senior Dev Mode) ---
Type "# 3. Senior Workflow: Scan only modified code"
Sleep 500ms
Enter
Type "vibecheck --staged --fast"
Sleep 500ms
Enter
Sleep 2s

# --- Scenario 4: Interactive Chat ---
Type "# 4. Interactive AI Tutor (REPL)"
Sleep 500ms
Enter
Type "vibecheck --chat"
Sleep 1s
Enter
Sleep 1s
Type "What is an SQL injection exactly?"
Sleep 500ms
Enter
Sleep 4s
Type "exit"
Enter

# --- Outro ---
Sleep 1s
Type "# Done. Your codebase is now audited."
Sleep 2s
