@echo off
chcp 65001 >nul
title Composer Engine - Tests

echo ========================================
echo   Composer Engine - Test Runner
echo ========================================
echo.

cd /d "%~dp0\.."

echo [1/2] Syncing dependencies (with dev)...
uv sync --quiet --extra dev
if %errorlevel% neq 0 (
    echo [ERROR] uv sync failed.
    pause
    exit /b 1
)

echo [2/2] Running tests...
echo.

if "%~1"=="" (
    uv run python -m pytest tests/ -v --tb=short
) else (
    uv run python -m pytest %*
)

echo.
echo ========================================
echo   Tests finished. Exit code: %errorlevel%
echo ========================================
pause
