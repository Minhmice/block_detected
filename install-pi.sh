#!/usr/bin/env bash
# Pi 5 lite deps — no CUDA / TensorRT from pip install -e ".[all]" or core pyproject.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

PY="${PYTHON:-python3}"

echo "==> Pi 5 profile: requirements-pi.txt + editable package (--no-deps)"
"$PY" -m pip install -U pip
"$PY" -m pip install -r requirements-pi.txt
"$PY" -m pip install -e . --no-deps

echo "==> Done. Run: python main.py --no-install --tui  (or --stream)"
