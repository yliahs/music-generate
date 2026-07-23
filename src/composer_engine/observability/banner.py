"""Startup banner for Composer Engine."""

import os
import platform
import sys


def print_banner(tool_count: int = 146, phase_count: int = 11) -> None:
    """Print startup banner to stderr (unless COMPOSER_NO_BANNER is set)."""
    if os.environ.get("COMPOSER_NO_BANNER"):
        return

    try:
        import pydantic
        pydantic_ver = pydantic.VERSION
    except Exception:
        pydantic_ver = "?"

    python_ver = platform.python_version()
    log_level = os.environ.get("COMPOSER_LOG_LEVEL", "INFO").upper()
    log_file = os.environ.get("COMPOSER_LOG_FILE", "")

    banner = f"""
╔══════════════════════════════════════════╗
║   🎵 Composer Engine v0.1.0             ║
║   MCP Tools: {tool_count:<4d}| Phases: {phase_count:<13d}║
║   Python: {python_ver:<8s}| Pydantic: {pydantic_ver:<8s}║
╚══════════════════════════════════════════╝"""

    print(banner, file=sys.stderr)
    print(f"  Log level: {log_level}", file=sys.stderr)
    if log_file:
        print(f"  Log file: {log_file}", file=sys.stderr)
    print(file=sys.stderr)
