function Write-Typewriter {
    param([string]$text, [int]$delay = 40, [string]$color = "Cyan")
    $text.ToCharArray() | ForEach-Object {
        Write-Host $_ -NoNewline -ForegroundColor $color
        Start-Sleep -Milliseconds $delay
    }
    Write-Host ""
}

# --- MULAI TRAILER v3.0 (THE ULTIMATE EDITION) ---
Clear-Host
Write-Host "`n"
$logo = @"
  __   __ _  _             ____  _                 _     
  \ \ / /(_)| |__    ___  / ___|| |__    ___   ___ | | __
   \ V / | || '_ \  / _ \| |    | '_ \  / _ \ / __|| |/ /
    \ /  | || |_) ||  __/| |___ | | | ||  __/| (__ |   < 
     V   |_||_.__/  \___| \____||_| |_| \___| \___||_|\_\
"@
Write-Host $logo -ForegroundColor Cyan
Write-Host "  >> THE VIRTUAL SENIOR DEVELOPER IN YOUR TERMINAL <<" -ForegroundColor DarkCyan
Write-Host "`n"

Start-Sleep -Milliseconds 800

# PHASE 1: THE BEGINNER TUTOR (ELI5)
Write-Typewriter "[1/4] TEACHING ABSOLUTE BEGINNERS..." 30 "Gray"
Write-Host "PS E:\VibeCheck> " -NoNewline
Write-Typewriter "vibecheck examples/python_bad.py --learn" 60 "White"
vibecheck examples/python_bad.py --learn
Start-Sleep -Seconds 2

# PHASE 2: PROJECT SPECIFIC CONTEXT
Write-Host "`n"
Write-Typewriter "[2/4] READING LOCAL PROJECT RULES..." 30 "Gray"
Write-Host "PS E:\VibeCheck> " -NoNewline
Write-Typewriter "Get-Content .vibecheck_rules.md | Select-Object -First 3" 60 "White"
Get-Content .vibecheck_rules.md | Select-Object -First 3 | ForEach-Object { Write-Host $_ -ForegroundColor DarkYellow }
Start-Sleep -Seconds 1
Write-Host "PS E:\VibeCheck> " -NoNewline
Write-Typewriter "vibecheck examples/python_bad.py" 60 "White"
vibecheck examples/python_bad.py
Start-Sleep -Seconds 2

# PHASE 3: THE SENIOR WORKFLOW (GIT STAGED)
Write-Host "`n"
Write-Typewriter "[3/4] THE SENIOR WORKFLOW (ZERO NOISE)..." 30 "Gray"
Write-Host "PS E:\VibeCheck> " -NoNewline
Write-Typewriter "git add examples/python_bad.py" 60 "White"
Write-Host "PS E:\VibeCheck> " -NoNewline
Write-Typewriter "vibecheck --staged --fast" 60 "White"
vibecheck examples/python_bad.py --fast
Start-Sleep -Seconds 2

# PHASE 4: INTERACTIVE REPL
Write-Host "`n"
Write-Typewriter "[4/4] INTERACTIVE CHAT MODE..." 30 "Gray"
Write-Host "PS E:\VibeCheck> " -NoNewline
Write-Typewriter "vibecheck --chat" 60 "White"
Write-Host "`n[bold bright_blue]💬 VibeCheck Interactive Mode (Type 'exit' to quit)[/bold bright_blue]" -ForegroundColor Cyan
Write-Host "You: " -ForegroundColor Green -NoNewline
Write-Typewriter "Can you fix the SQL injection for me?" 60 "White"
Write-Host "VibeCheck: " -ForegroundColor Magenta -NoNewline
Write-Typewriter "Sure! Replace line 42 with: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))" 40 "White"
Start-Sleep -Seconds 2

Write-Host "`n" + ("=" * 60) -ForegroundColor DarkCyan
Write-Typewriter "VIBECHECK: YOUR CODEBASE IS NOW SECURE." 40 "Yellow"
Write-Typewriter "READY FOR ENTERPRISE DEPLOYMENT." 40 "Green"
Write-Host ("=" * 60) -ForegroundColor DarkCyan
Write-Host "`nInstall now: pip install vibecheck-ai-tool" -ForegroundColor White
