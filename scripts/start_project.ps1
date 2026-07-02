param(
    [switch]$SkipOllama,
    [switch]$SkipDashboard,
    [switch]$NoInitDb,
    [switch]$IngestWatchlist,
    [string]$Period = "1y",
    [int]$DashboardPort = 8501,
    [int]$OllamaPort = 11434
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$RuntimeDir = Join-Path $RepoRoot ".runtime"
$PidDir = Join-Path $RuntimeDir "pids"
$LogDir = Join-Path $RepoRoot "logs"
New-Item -ItemType Directory -Force -Path $PidDir, $LogDir | Out-Null

function Test-PortOpen {
    param([int]$Port)
    $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1
    return $null -ne $connection
}

function Get-RepoPython {
    $venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) { return $venvPython }
    return "python"
}

function Start-LoggedProcess {
    param(
        [string]$Name,
        [string]$FilePath,
        [string[]]$ArgumentList,
        [string]$PidFile
    )
    $stdout = Join-Path $LogDir "$Name.out.log"
    $stderr = Join-Path $LogDir "$Name.err.log"
    $process = Start-Process `
        -FilePath $FilePath `
        -ArgumentList $ArgumentList `
        -WorkingDirectory $RepoRoot `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr `
        -PassThru `
        -WindowStyle Hidden
    Set-Content -Path $PidFile -Value $process.Id
    Write-Host "Started $Name with PID $($process.Id). Logs: logs/$Name.out.log and logs/$Name.err.log"
}

Set-Location $RepoRoot
$python = Get-RepoPython

if (-not $NoInitDb) {
    Write-Host "Initializing DuckDB schema..."
    & $python -m app.main init-db
}

if ($IngestWatchlist) {
    Write-Host "Ingesting default watchlist for period $Period..."
    & $python -m app.main ingest-watchlist --period $Period
}

if (-not $SkipOllama) {
    if (Test-PortOpen -Port $OllamaPort) {
        Write-Host "Ollama already appears to be running on port $OllamaPort."
    }
    else {
        $ollamaCommand = Get-Command ollama -ErrorAction SilentlyContinue
        if ($null -eq $ollamaCommand) {
            Write-Host "Ollama command not found. Install Ollama or start it manually before using Gemma analysis." -ForegroundColor Yellow
        }
        else {
            Start-LoggedProcess `
                -Name "ollama" `
                -FilePath $ollamaCommand.Source `
                -ArgumentList @("serve") `
                -PidFile (Join-Path $PidDir "ollama.pid")
            Start-Sleep -Seconds 3
        }
    }
}

if (-not $SkipDashboard) {
    if (Test-PortOpen -Port $DashboardPort) {
        Write-Host "Streamlit dashboard already appears to be running on port $DashboardPort."
    }
    else {
        Start-LoggedProcess `
            -Name "streamlit" `
            -FilePath $python `
            -ArgumentList @("-m", "streamlit", "run", "app/dashboard/streamlit_app.py", "--server.port", "$DashboardPort", "--server.headless", "true") `
            -PidFile (Join-Path $PidDir "streamlit.pid")
        Start-Sleep -Seconds 3
    }
}

Write-Host ""
Write-Host "Project start command completed."
Write-Host "Dashboard: http://localhost:$DashboardPort"
Write-Host "Run .\scripts\status_project.ps1 to check services."
