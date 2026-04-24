function Write-Typewriter {
    param([string]$text, [int]$delay = 40, [string]$color = "Cyan")
    $text.ToCharArray() | ForEach-Object {
        Write-Host $_ -NoNewline -ForegroundColor $color
        Start-Sleep -Milliseconds $delay
    }
    Write-Host ""
}

# --- MULAI TRAILER v2.0 ---
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
Write-Host "  >> SECURING YOUR VIBE, ONE LINE AT A TIME <<" -ForegroundColor DarkCyan
Write-Host "`n"

Start-Sleep -Milliseconds 800

# PHASE 1: INDIVIDUAL SCAN
Write-Typewriter "[1/3] TARGETING HOTSPOTS..." 30 "Gray"
Write-Host "PS E:\VibeCheck> " -NoNewline
Write-Typewriter "vibecheck examples/python_bad.py" 80 "White"
vibecheck examples/python_bad.py
Start-Sleep -Seconds 2

# PHASE 2: PROJECT HEALTH (DEBT)
Write-Host "`n"
Write-Typewriter "[2/3] CALCULATING TECHNICAL DEBT..." 30 "Gray"
Write-Host "PS E:\VibeCheck> " -NoNewline
Write-Typewriter "vibecheck --debt examples/" 80 "White"
vibecheck --debt examples/
Start-Sleep -Seconds 2

# PHASE 3: MEMORY & LEARNING
Write-Host "`n"
Write-Typewriter "[3/3] ACCESSING PROJECT MEMORY..." 30 "Gray"
Write-Host "PS E:\VibeCheck> " -NoNewline
Write-Typewriter "vibecheck --memory" 80 "White"
Write-Host "`n>> MENTAL MAP LOADED" -ForegroundColor Green
Write-Host ">> LOG: REMEMBERED SQL INJECTION FIX FROM 2 HOURS AGO" -ForegroundColor Gray
Write-Host ">> LOG: ARCHITECTURAL PATTERN RECOGNIZED: FLASK-API" -ForegroundColor Gray
Start-Sleep -Seconds 1

Write-Host "`n" + ("=" * 50) -ForegroundColor DarkCyan
Write-Typewriter "VIBECHECK: YOUR PROJECT IS NOW AUDITED." 40 "Yellow"
Write-Typewriter "READY FOR PRODUCTION." 40 "Green"
Write-Host ("=" * 50) -ForegroundColor DarkCyan
Write-Host "`nLaunch with Confidence." -ForegroundColor White
