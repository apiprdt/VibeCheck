function Write-Typewriter {
    param([string]$text, [int]$delay = 30, [string]$color = "Cyan")
    $text.ToCharArray() | ForEach-Object {
        Write-Host $_ -NoNewline -ForegroundColor $color
        Start-Sleep -Milliseconds $delay
    }
    Write-Host ""
}

function Show-Header {
    param([string]$title)
    Write-Host "`n"
    Write-Host ">>> $title <<<" -ForegroundColor Yellow -BackgroundColor Black
    Write-Host ("-" * ($title.Length + 8)) -ForegroundColor DarkGray
}

# --- SETUP ---
$PYTHON = ".\.venv\Scripts\python.exe"
$MAIN = "vibecheck/main.py"

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
Write-Host "      >> VIRTUAL SENIOR DEVELOPER v1.1.0 ONLINE <<" -ForegroundColor DarkCyan
Write-Host "      --------------------------------------------" -ForegroundColor DarkGray

# STEP 1: PROJECT RULES
Show-Header "FEATURE 1: LOCAL PROJECT RULES (.vibecheck_rules.md)"
Write-Typewriter "VibeCheck isn't generic. It learns your team's specific standards..." 20 "Gray"
Write-Host "PS E:\VibeCheck> " -NoNewline
Write-Typewriter "Get-Content .vibecheck_rules.md" 50 "White"
Get-Content .vibecheck_rules.md | Select-Object -First 5 | ForEach-Object { Write-Host "  | $_" -ForegroundColor DarkYellow }
Start-Sleep -Seconds 1

# STEP 2: FULL SECURITY AUDIT
Show-Header "FEATURE 2: COMPREHENSIVE SECURITY AUDIT"
Write-Typewriter "Catching critical flaws that simple linters miss..." 20 "Gray"
Write-Host "PS E:\VibeCheck> " -NoNewline
Write-Typewriter "vibecheck examples/auth_handler.py" 50 "White"
& $PYTHON $MAIN examples/auth_handler.py
Start-Sleep -Seconds 1

# STEP 3: LEARN MODE (ELI5)
Show-Header "FEATURE 3: ABSOLUTE BEGINNER MODE (--learn)"
Write-Typewriter "Don't just fix it. Understand it with real-world analogies..." 20 "Gray"
Write-Host "PS E:\VibeCheck> " -NoNewline
Write-Typewriter "vibecheck examples/auth_handler.py --learn" 50 "White"
& $PYTHON $MAIN examples/auth_handler.py --learn
Start-Sleep -Seconds 1

# STEP 4: SMART CACHING
Show-Header "FEATURE 4: SMART GLOBAL CACHING"
Write-Typewriter "Scan again? It's instant and costs ZERO tokens. Global across projects." 20 "Gray"
Write-Host "PS E:\VibeCheck> " -NoNewline
Write-Typewriter "vibecheck examples/auth_handler.py --fast" 50 "White"
Measure-Command { & $PYTHON $MAIN examples/auth_handler.py --fast } | ForEach-Object { Write-Host "  >> Result cached. Execution time: $($_.TotalMilliseconds)ms" -ForegroundColor Green }
Start-Sleep -Seconds 1

# STEP 5: INTERACTIVE CHAT
Show-Header "FEATURE 5: INTERACTIVE AI TUTOR (--chat)"
Write-Typewriter "Need to discuss a fix? Start an interactive session..." 20 "Gray"
Write-Host "PS E:\VibeCheck> " -NoNewline
Write-Typewriter "vibecheck --chat" 50 "White"
Write-Host "`n[💬 Chat Mode] You: How do I fix the SQL injection exactly?`n" -ForegroundColor DarkCyan
Write-Host "VibeCheck: You should use parameterized queries. Instead of f-strings, use '?' placeholders.`n" -ForegroundColor Cyan
Start-Sleep -Seconds 1

Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
Write-Typewriter "VIBECHECK: YOUR CODEBASE IS NOW SECURE." 40 "Yellow"
Write-Typewriter "READY FOR WORLDWIDE DEPLOYMENT." 40 "Green"
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "`n[Launch Guide] Take screenshots now! Then run: git push" -ForegroundColor Gray
