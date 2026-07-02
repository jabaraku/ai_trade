#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="$REPO_ROOT/.runtime"
PID_DIR="$RUNTIME_DIR/pids"
LOG_DIR="$REPO_ROOT/logs"
DASHBOARD_PORT="${DASHBOARD_PORT:-8501}"
OLLAMA_PORT="${OLLAMA_PORT:-11434}"
PERIOD="${PERIOD:-1y}"
SKIP_OLLAMA="${SKIP_OLLAMA:-0}"
SKIP_DASHBOARD="${SKIP_DASHBOARD:-0}"
NO_INIT_DB="${NO_INIT_DB:-0}"
INGEST_WATCHLIST="${INGEST_WATCHLIST:-0}"

mkdir -p "$PID_DIR" "$LOG_DIR"
cd "$REPO_ROOT"

PYTHON_BIN="$REPO_ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python"
fi

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

if [[ "$NO_INIT_DB" != "1" ]]; then
  echo "Initializing DuckDB schema..."
  "$PYTHON_BIN" -m app.main init-db
fi

if [[ "$INGEST_WATCHLIST" == "1" ]]; then
  echo "Ingesting default watchlist for period $PERIOD..."
  "$PYTHON_BIN" -m app.main ingest-watchlist --period "$PERIOD"
fi

if [[ "$SKIP_OLLAMA" != "1" ]]; then
  if port_open "$OLLAMA_PORT"; then
    echo "Ollama already appears to be running on port $OLLAMA_PORT."
  elif command -v ollama >/dev/null 2>&1; then
    echo "Starting Ollama..."
    nohup ollama serve > "$LOG_DIR/ollama.out.log" 2> "$LOG_DIR/ollama.err.log" &
    echo $! > "$PID_DIR/ollama.pid"
    sleep 3
  else
    echo "Ollama command not found. Install/start Ollama manually before using Gemma analysis." >&2
  fi
fi

if [[ "$SKIP_DASHBOARD" != "1" ]]; then
  if port_open "$DASHBOARD_PORT"; then
    echo "Streamlit dashboard already appears to be running on port $DASHBOARD_PORT."
  else
    echo "Starting Streamlit dashboard..."
    nohup "$PYTHON_BIN" -m streamlit run app/dashboard/streamlit_app.py --server.port "$DASHBOARD_PORT" --server.headless true > "$LOG_DIR/streamlit.out.log" 2> "$LOG_DIR/streamlit.err.log" &
    echo $! > "$PID_DIR/streamlit.pid"
    sleep 3
  fi
fi

echo ""
echo "Project start command completed."
echo "Dashboard: http://localhost:$DASHBOARD_PORT"
echo "Run ./scripts/status_project.sh to check services."
