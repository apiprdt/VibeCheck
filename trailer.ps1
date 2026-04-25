function Write-Typewriter {
    param([string]$text, [int]$delay = 40, [string]$color = "Cyan")
    $text.ToCharArray() | ForEach-Object {
        Write-Host $_ -NoNewline -ForegroundColor $color
        Start-Sleep -Milliseconds $delay
    }
    Write-Host ""
}

# --- MULAI TRAILER v4.0 (CINEMATIC EDITION) ---
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
Write-Host "      >> THE VIRTUAL SENIOR DEVELOPER IS NOW ONLINE <<" -ForegroundColor DarkCyan
Write-Host "      ------------------------------------------------" -ForegroundColor DarkGray
Write-Host "`n"

Start-Sleep -Milliseconds 800

# PHASE 1: SYSTEM CHECK
Write-Typewriter "[+] SYSTEM: VibeCheck v1.0.0" 20 "Gray"
Write-Typewriter "[+] STATUS: Ready for Audit" 20 "Gray"
Write-Typewriter "[+] ENGINE: Llama 3.3 70B (Groq)" 20 "Gray"
Write-Host "`n"

# PHASE 2: THE COMMAND
Write-Host "PS E:\VibeCheck> " -NoNewline
Write-Typewriter "vibecheck examples/python_bad.py --learn" 60 "White"
Write-Host "`n"
Write-Typewriter "Analyzing codebase architecture..." 40 "DarkCyan"
Write-Typewriter "Applying local project rules (.vibecheck_rules.md)..." 40 "DarkCyan"
Write-Typewriter "Consulting virtual senior developer memory..." 40 "DarkCyan"

Write-Host "`n"
Write-Host "--------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "  >> AUDIT COMPLETE: 2 CRITICAL, 3 WARNINGS FOUND <<" -ForegroundColor Red
Write-Host "--------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "`n"

Write-Typewriter "VibeCheck is ready. Are you?" 80 "Yellow"
Write-Host "`n"
