@echo off
chcp 65001 >nul
title Composer Engine - MCP Server

echo ========================================
echo   Composer Engine - MCP Server
echo   143 MCP Tools / 10 Phases
echo ========================================
echo.

cd /d "%~dp0\.."

echo [1/2] Syncing dependencies...
uv sync --quiet
if %errorlevel% neq 0 (
    echo [ERROR] uv sync failed. Is uv installed?
    echo   Install: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    pause
    exit /b 1
)

echo [2/2] Starting MCP Server...
echo.
uv run python -m composer_engine.server.mcp_server
pause
