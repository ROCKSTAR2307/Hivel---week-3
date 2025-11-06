from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_FILE = LOG_DIR / "activity.log"


def _write(kind: str, payload: str) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    line = f"{timestamp} [{kind.upper()}] {payload}"
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def log_agent_start(agent_name: str) -> None:
    _write("agent", f"agent={agent_name} status=started")


def log_user_query(agent_name: str, query: str) -> None:
    _write("query", f"agent={agent_name} prompt={query!r}")


def log_tool_call(tool_name: str, **kwargs: Any) -> None:
    extras = " ".join(f"{key}={value!r}" for key, value in kwargs.items() if value is not None)
    payload = f"tool={tool_name}"
    if extras:
        payload = f"{payload} {extras}"
    _write("tool", payload)


def log_sql(statement: str) -> None:
    condensed = " ".join(statement.split())
    _write("sql", condensed)
