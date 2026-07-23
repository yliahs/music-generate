"""Runtime statistics collector for Composer Engine."""

import time
from datetime import datetime, timezone


class ServerStats:
    """Collects and reports runtime statistics."""

    def __init__(self):
        self.start_time: float = time.time()
        self.tool_calls: int = 0
        self.tool_errors: int = 0
        self.commands_executed: int = 0
        self.undo_count: int = 0
        self.redo_count: int = 0
        self.last_tool: str = ""
        self.last_tool_time: str = ""

    def record_tool_call(self, tool_name: str, success: bool, elapsed_ms: float) -> None:
        self.tool_calls += 1
        if not success:
            self.tool_errors += 1
        status = "OK" if success else "FAIL"
        self.last_tool = f"{tool_name} ({status}) {elapsed_ms:.0f}ms"
        self.last_tool_time = datetime.now(timezone.utc).isoformat()

    def record_command(self) -> None:
        self.commands_executed += 1

    def record_undo(self) -> None:
        self.undo_count += 1

    def record_redo(self) -> None:
        self.redo_count += 1

    def get_uptime(self) -> str:
        elapsed = time.time() - self.start_time
        h = int(elapsed // 3600)
        m = int(elapsed % 3600 // 60)
        s = int(elapsed % 60)
        return f"{h}h {m}m {s}s"

    def to_dict(self) -> dict:
        return {
            "uptime": self.get_uptime(),
            "tool_calls": self.tool_calls,
            "tool_errors": self.tool_errors,
            "error_rate": f"{(self.tool_errors / max(1, self.tool_calls) * 100):.1f}%",
            "commands_executed": self.commands_executed,
            "undo_count": self.undo_count,
            "redo_count": self.redo_count,
            "last_tool": self.last_tool,
            "last_tool_time": self.last_tool_time,
        }
