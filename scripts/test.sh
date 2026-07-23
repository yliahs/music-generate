#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo "  Composer Engine - Test Runner"
echo "========================================"
echo

cd "$(dirname "$0")/.."

echo "[1/2] Syncing dependencies (with dev)..."
uv sync --quiet --extra dev || {
    echo "[ERROR] uv sync failed."
    exit 1
}

echo "[2/2] Running tests..."
echo

if [ $# -eq 0 ]; then
    uv run python -m pytest tests/ -v --tb=short
else
    uv run python -m pytest "$@"
fi

echo
echo "========================================"
echo "  Tests finished."
echo "========================================"
