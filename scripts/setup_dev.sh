#!/usr/bin/env bash
# First-time dev setup: Python 3.11 venv, deps, env files, npm.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

FORCE=0
if [[ "${1:-}" == "--force" ]]; then
  FORCE=1
fi

find_python311() {
  if command -v python3.11 >/dev/null 2>&1; then
    command -v python3.11
    return 0
  fi
  if command -v brew >/dev/null 2>&1; then
    local brew_py
    brew_py="$(brew --prefix python@3.11 2>/dev/null)/bin/python3.11"
    if [[ -x "$brew_py" ]]; then
      echo "$brew_py"
      return 0
    fi
  fi
  return 1
}

PY311="$(find_python311)" || {
  echo "ERROR: Python 3.11 not found."
  echo "Install with: brew install python@3.11"
  exit 1
}

echo "Using Python: $PY311 ($("$PY311" --version))"

if [[ -d .venv ]]; then
  venv_py="$(.venv/bin/python --version 2>&1 || true)"
  if [[ "$venv_py" != *"3.11"* ]]; then
    if [[ "$FORCE" -eq 1 ]]; then
      echo "Removing existing venv ($venv_py)..."
      rm -rf .venv
    else
      echo "ERROR: .venv exists but is not Python 3.11 ($venv_py)."
      echo "Re-run with: make setup FORCE=1   or   ./scripts/setup_dev.sh --force"
      exit 1
    fi
  fi
fi

if [[ ! -d .venv ]]; then
  echo "Creating .venv with Python 3.11..."
  "$PY311" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

pip install -U pip wheel
pip install -e ".[dev]"
pip install -r backend/requirements-dev.txt

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

if [[ ! -f frontend/.env.local ]]; then
  cp frontend/.env.local.example frontend/.env.local
  echo "Created frontend/.env.local"
fi

npm install
(cd frontend && npm install)

echo ""
echo "Setup complete."
echo "  make dev     → http://localhost:3000 + backend :8000"
echo "  make doctor  → check venv and env"
echo "  source .venv/bin/activate"
