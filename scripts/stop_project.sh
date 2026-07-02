#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="$REPO_ROOT/.runtime/pids"

stop_pid_file() {
  local name="$1"
  local pid_file="$2"
  if [[ ! -f "$pid_file" ]]; then
    echo "No tracked PID file for $name."
    return
  fi
  local pid
  pid="$(cat "$pid_file")"
  if kill -0 "$pid" >/dev/null 2>&1; then
    echo "Stopping tracked $name process with PID $pid..."
    kill "$pid" || true
    sleep 1
    if kill -0 "$pid" >/dev/null 2>&1; then
      kill -9 "$pid" || true
    fi
  fi
  rm -f "$pid_file"
}

stop_pid_file "streamlit" "$PID_DIR/streamlit.pid"
stop_pid_file "ollama" "$PID_DIR/ollama.pid"

echo "Project shutdown command completed."
