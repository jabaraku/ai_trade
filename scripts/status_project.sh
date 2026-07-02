#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="$REPO_ROOT/.runtime/pids"
DASHBOARD_PORT="${DASHBOARD_PORT:-8501}"
OLLAMA_PORT="${OLLAMA_PORT:-11434}"

port_open() {
  local port="$1"
  python - "$port" <<'PY'
import socket, sys
port = int(sys.argv[1])
s = socket.socket()
s.settimeout(0.5)
try:
    s.connect(("127.0.0.1", port))
except OSError:
    sys.exit(1)
finally:
    s.close()
sys.exit(0)
PY
}

status_for() {
  local name="$1"
  local port="$2"
  local pid_file="$3"
  local state="stopped"
  if port_open "$port"; then state="running"; fi
  local pid=""
  if [[ -f "$pid_file" ]]; then pid="$(cat "$pid_file")"; fi
  printf "%-22s port=%-6s status=%-8s tracked_pid=%s\n" "$name" "$port" "$state" "$pid"
}

status_for "Streamlit dashboard" "$DASHBOARD_PORT" "$PID_DIR/streamlit.pid"
status_for "Ollama / Gemma" "$OLLAMA_PORT" "$PID_DIR/ollama.pid"
