param(
    [switch]$ForceByPort,
    [switch]$StopExternalOllama,
    [int]$DashboardPort = 8501,
    [int]$OllamaPort = 11434
)

$RepoRoot = Split-Path -Parent $PSScriptRoot
$PidDir = Join-Path $RepoRoot ".runtime\pids"

function Stop-TrackedProcess {
    param([string]$Name)
    $pidFile = Join-Path $PidDir "$Name.pid"
    if (-not (Test-Path $pidFile)) {
        Write-Host "No tracked PID file for $Name."
        return
    }
    $pidValue = Get-Content $pidFile | Select-Object -First 1
    $process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
    if ($null -ne $process) {
        Write-Host "Stopping tracked $Name process with PID $pidValue..."
        Stop-Process -Id $pidValue -Force -ErrorAction SilentlyContinue
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}

function Stop-PortProcess {
    param([int]$Port, [string]$Name)
    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    foreach ($connection in $connections) {
        $pidValue = $connection.OwningProcess
        if ($pidValue) {
            Write-Host "Stopping $Name process on port $Port with PID $pidValue..."
            Stop-Process -Id $pidValue -Force -ErrorAction SilentlyContinue
        }
    }
}

Stop-TrackedProcess -Name "streamlit"
Stop-TrackedProcess -Name "ollama"

if ($ForceByPort) {
    Stop-PortProcess -Port $DashboardPort -Name "Streamlit dashboard"
}

if ($StopExternalOllama) {
    Stop-PortProcess -Port $OllamaPort -Name "Ollama"
}

Write-Host "Project shutdown command completed."
Write-Host "Tip: use -ForceByPort to kill an untracked Streamlit process; use -StopExternalOllama to kill Ollama even if this project did not start it."
