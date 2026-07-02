param(
    [int]$DashboardPort = 8501,
    [int]$OllamaPort = 11434
)

$RepoRoot = Split-Path -Parent $PSScriptRoot
$PidDir = Join-Path $RepoRoot ".runtime\pids"

function Get-PortProcess {
    param([int]$Port)
    $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $connection) { return $null }
    return Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
}

function Get-TrackedPid {
    param([string]$Name)
    $file = Join-Path $PidDir "$Name.pid"
    if (-not (Test-Path $file)) { return $null }
    return (Get-Content $file | Select-Object -First 1)
}

$rows = @(
    [pscustomobject]@{
        Component = "Streamlit dashboard"
        Port = $DashboardPort
        PortStatus = if (Get-PortProcess -Port $DashboardPort) { "running" } else { "stopped" }
        TrackedPid = Get-TrackedPid -Name "streamlit"
    },
    [pscustomobject]@{
        Component = "Ollama / Gemma"
        Port = $OllamaPort
        PortStatus = if (Get-PortProcess -Port $OllamaPort) { "running" } else { "stopped" }
        TrackedPid = Get-TrackedPid -Name "ollama"
    }
)

$rows | Format-Table -AutoSize
