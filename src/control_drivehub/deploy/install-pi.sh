#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY="${PYTHON:-python3}"
NODE="${NODE:-node}"
NPM="${NPM:-npm}"

echo "==> Creating Python venv"
$PY -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r pi_monitor/requirements.txt

echo "==> Building Next.js dashboard"
cd dashboard
$NPM ci
$NPM run build
cd "$ROOT"

echo "==> Preparing config"
if [ ! -f pi_monitor/config.yaml ]; then
  cp pi_monitor/config.example.yaml pi_monitor/config.yaml
fi

echo "==> Installing systemd units"
sudo cp deploy/pimonitor-api.service /etc/systemd/system/
sudo cp deploy/pimonitor-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pimonitor-api.service pimonitor-dashboard.service
sudo systemctl restart pimonitor-api.service pimonitor-dashboard.service

echo "Done. Dashboard: http://$(hostname -I | awk '{print $1}'):3000"
