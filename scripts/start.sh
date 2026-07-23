#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo "  Composer Engine - MCP Server"
echo "  143 MCP Tools / 10 Phases"
echo "========================================"
echo

cd "$(dirname "$0")/.."

echo "[1/2] Syncing dependencies..."
uv sync --quiet || {
    echo "[ERROR] uv sync failed. Is uv installed?"
    echo "  Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
}

echo "[2/2] Starting MCP Server..."
echo
exec uv run python -m composer_engine.server.mcp_server
