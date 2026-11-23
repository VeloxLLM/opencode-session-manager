"""Database layer for OpenCode Session Manager (OpenCode v2 only).

Only the v2 tables are used:

* ``session_v2``    - sessions
* ``session_message`` / ``session_part`` - messages and parts

Table names are constants; all values are passed as SQL parameters.
"""

from __future__ import annotations

import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set

V2_TABLE = "session_v2"
MESSAGE_TABLE = "session_message"
PART_TABLE = "session_part"
ARCHIVE_FORMAT = "opencode-session-manager"
ARCHIVE_VERSION = 2

_SESSION_COLUMNS = (
    "id",
    "title",
    "directory",
    "project_id",
    "version",
    "time_created",
    "time_updated",
    "time_archived",
    "cost",
    "tokens_input",
    "tokens_output",
)


@dataclass(frozen=True)
class SessionRef:
    """Reference to a v2 session row. ``table`` is kept in archive payloads."""

    id: str
    table: str = V2_TABLE

    @property
    def key(self) -> str:
        return f"{self.table}:{self.id}"

    @classmethod
    def parse(cls, key: str) -> "SessionRef":
        table, sep, sid = str(key).partition(":")
        if not sep or table != V2_TABLE or not sid:
            raise ValueError(f"Invalid v2 session reference: {key!r}")
        return cls(id=sid, table=V2_TABLE)


@dataclass
class SessionInfo:
    ref: SessionRef
    title: str
    directory: str
    project_id: str
    version: str
    time_created: int
    time_updated: int
    time_archived: Optional[int]
    message_count: int
    cost: float
    tokens_input: int
    tokens_output: int

    @property
    def is_archived(self) -> bool:
        return self.time_archived is not None

    @property
    def tokens_total(self) -> int:
        return (self.tokens_input or 0) + (self.tokens_output or 0)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "table": self.ref.table,
            "id": self.ref.id,
            "title": self.title,
            "directory": self.directory,
            "project_id": self.project_id,
            "version": self.version,
            "time_created": self.time_created,
            "time_updated": self.time_updated,
            "time_archived": self.time_archived,
            "message_count": self.message_count,
            "cost": self.cost,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
        }


def candidate_database_paths() -> List[Path]:
    """Return likely OpenCode v2 database paths, most specific first."""
    candidates: List[Path] = []

    override = os.environ.get("OPENCODE_SESSION_MANAGER_DB")
    if override:
        candidates.append(Path(override).expanduser())

    data_home = os.environ.get("XDG_DATA_HOME")
    if data_home:
        candidates.append(Path(data_home).expanduser() / "opencode" / "opencode.db")

    candidates.extend(
        [
            Path.home() / ".local" / "share" / "opencode" / "opencode.db",
            Path(os.environ.get("LOCALAPPDATA", "")) / "opencode" / "opencode.db",
            Path(os.environ.get("APPDATA", "")) / "opencode" / "opencode.db",
        ]
    )

    seen: Set[str] = set()
    result: List[Path] = []
    for path in candidates:
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            result.append(path)
    return result


def find_database() -> Optional[Path]:
    for path in candidate_database_paths():
        if path.is_file():
            return path
    return None


def connect(path: Path, *, read_only: bool = False) -> sqlite3.Connection:
    if read_only:
        uri = Path(path).expanduser().resolve().as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=10)
    else:
        conn = sqlite3.connect(str(Path(path).expanduser()), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


def table_names(conn: sqlite3.Connection) -> Set[str]:
    return {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def is_v2_database(conn: sqlite3.Connection) -> bool:
    return V2_TABLE in table_names(conn)


def detect_schema(conn: sqlite3.Connection) -> Dict[str, Any]:
    return {"v2": is_v2_database(conn), "tables": sorted(table_names(conn))}


def _columns(conn: sqlite3.Connection, table: str) -> Set[str]:
    if table not in table_names(conn):
        return set()
    return {row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')}


def _now_ms() -> int:
    return int(time.time() * 1000)


def _time_threshold_ms(time_range: str) -> Optional[int]:
    now = _now_ms()
    if time_range == "today":
        midnight = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return int(midnight.timestamp() * 1000)
    if time_range == "7d":
        return now - 7 * 24 * 60 * 60 * 1000
    if time_range == "30d":
        return now - 30 * 24 * 60 * 60 * 1000
    return None


def list_sessions(
    conn: sqlite3.Connection,
    *,
    status: str = "all",
    time_range: str = "all",
    search: str = "",
) -> List[SessionInfo]:
    """Return v2 sessions, newest first."""
    if not is_v2_database(conn):
        return []

    names = table_names(conn)
    threshold = _time_threshold_ms(time_range)
    needle = search.strip().lower()
    available = _columns(conn, V2_TABLE)
    selected = [column for column in _SESSION_COLUMNS if column in available]
    if "id" not in selected:
        return []

    rows = conn.execute(f'SELECT {", ".join(selected)} FROM "{V2_TABLE}"').fetchall()
    result: List[SessionInfo] = []
    for row in rows:
        data = dict(row)
        updated = int(data.get("time_updated") or 0)
        archived = data.get("time_archived")
        if status == "active" and archived is not None:
            continue
        if status == "archived" and archived is None:
            continue
        if threshold is not None and updated < threshold:
            continue

        title = str(data.get("title") or "")
        directory = str(data.get("directory") or "")
        sid = str(data.get("id") or "")
        if needle and needle not in " ".join(
            (title, directory, sid, str(data.get("project_id") or ""))
        ).lower():
            continue

        count = 0
        if MESSAGE_TABLE in names:
            count = conn.execute(
                f'SELECT COUNT(*) FROM "{MESSAGE_TABLE}" WHERE session_id = ?', (sid,)
            ).fetchone()[0]

        result.append(
            SessionInfo(
                ref=SessionRef(id=sid),
                title=title or "(untitled)",
                directory=directory,
                project_id=str(data.get("project_id") or ""),
                version=str(data.get("version") or ""),
                time_created=int(data.get("time_created") or 0),
                time_updated=updated,
                time_archived=int(archived) if archived is not None else None,
                message_count=count,
                cost=float(data.get("cost") or 0.0),
                tokens_input=int(data.get("tokens_input") or 0),
                tokens_output=int(data.get("tokens_output") or 0),
            )
        )

    result.sort(key=lambda item: item.time_updated, reverse=True)
    return result


def get_database_summary(conn: sqlite3.Connection, path: Path) -> Dict[str, Any]:
    names = table_names(conn)
    sessions = 0
    archived = 0
    if V2_TABLE in names:
        sessions = conn.execute(f'SELECT COUNT(*) FROM "{V2_TABLE}"').fetchone()[0]
        if "time_archived" in _columns(conn, V2_TABLE):
            archived = conn.execute(
                f'SELECT COUNT(*) FROM "{V2_TABLE}" WHERE time_archived IS NOT NULL'
            ).fetchone()[0]

    try:
        size = Path(path).stat().st_size
    except OSError:
        size = 0
    return {
        "path": str(path),
        "size_bytes": size,
        "sessions": sessions,
        "archived": archived,
        "schema": detect_schema(conn),
    }


def export_sessions(conn: sqlite3.Connection, refs: Sequence[SessionRef]) -> Dict[str, Any]:
    """Export complete v2 session rows with their messages and parts."""
    names = table_names(conn)
    payload: Dict[str, Any] = {
        "format": ARCHIVE_FORMAT,
        "version": ARCHIVE_VERSION,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "source": "",
        "sessions": [],
    }
    for ref in refs:
        row = conn.execute(
            f'SELECT * FROM "{V2_TABLE}" WHERE id = ?', (ref.id,)
        ).fetchone()
        if row is None:
            continue
        item: Dict[str, Any] = {"table": V2_TABLE, "row": dict(row), "messages": [], "parts": []}
        if MESSAGE_TABLE in names:
            item["messages"] = [
                dict(message)
                for message in conn.execute(
                    f'SELECT * FROM "{MESSAGE_TABLE}" WHERE session_id = ? ORDER BY seq',
                    (ref.id,),
                )
            ]
        if PART_TABLE in names:
            item["parts"] = [
                dict(part)
                for part in conn.execute(
                    f'SELECT * FROM "{PART_TABLE}" WHERE session_id = ?', (ref.id,)
                )
            ]
        payload["sessions"].append(item)
    return payload


def _insert_row(
    conn: sqlite3.Connection,
    table: str,
    row: Dict[str, Any],
    allowed_tables: Set[str],
) -> int:
    if table not in allowed_tables or table not in table_names(conn):
        return 0
    existing = _columns(conn, table)
    values = {key: value for key, value in row.items() if key in existing}
    if not values:
        return 0
    columns = ", ".join(f'"{key}"' for key in values)
    placeholders = ", ".join("?" for _ in values)
    conn.execute(
        f'INSERT OR REPLACE INTO "{table}" ({columns}) VALUES ({placeholders})',
        tuple(values.values()),
    )
    return 1


def import_archive(conn: sqlite3.Connection, payload: Dict[str, Any]) -> Dict[str, int]:
    """Import a v2 full-session archive."""
    result = {"sessions": 0, "messages": 0, "parts": 0}
    if not isinstance(payload, dict) or payload.get("version") != ARCHIVE_VERSION:
        raise ValueError("Only v2 session archives are supported")
    if not isinstance(payload.get("sessions"), list):
        raise ValueError("Unsupported archive format")
    names = table_names(conn)
    if V2_TABLE not in names:
        raise ValueError("Target database is not an OpenCode v2 database")

    was_enabled = bool(conn.execute("PRAGMA foreign_keys").fetchone()[0])
    conn.commit()
    if was_enabled:
        conn.execute("PRAGMA foreign_keys = OFF")

    try:
        for item in payload["sessions"]:
            if not isinstance(item, dict):
                continue
            row = item.get("row")
            if item.get("table") != V2_TABLE or not isinstance(row, dict):
                continue

            project_id = row.get("project_id")
            if project_id and "project" in names:
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO project "
                        "(id, worktree, vcs, name, time_created, time_updated, sandboxes) "
                        "VALUES (?, ?, NULL, NULL, ?, ?, '[]')",
                        (
                            str(project_id),
                            str(row.get("directory") or "/"),
                            int(row.get("time_created") or _now_ms()),
                            int(row.get("time_updated") or _now_ms()),
                        ),
                    )
                except sqlite3.Error:
                    pass

            result["sessions"] += _insert_row(conn, V2_TABLE, row, {V2_TABLE})
            for message in item.get("messages", []):
                if isinstance(message, dict):
                    result["messages"] += _insert_row(
                        conn, MESSAGE_TABLE, message, {MESSAGE_TABLE}
                    )
            for part in item.get("parts", []):
                if isinstance(part, dict):
                    result["parts"] += _insert_row(conn, PART_TABLE, part, {PART_TABLE})
        conn.commit()
    finally:
        if was_enabled:
            conn.execute("PRAGMA foreign_keys = ON")
    return result


def delete_sessions(conn: sqlite3.Connection, refs: Sequence[SessionRef]) -> int:
    """Delete v2 sessions with foreign keys enforced."""
    if not is_v2_database(conn) or not refs:
        return 0
    conn.commit()
    was_enabled = bool(conn.execute("PRAGMA foreign_keys").fetchone()[0])
    if not was_enabled:
        conn.execute("PRAGMA foreign_keys = ON")
    deleted = 0
    try:
        for ref in refs:
            cursor = conn.execute(
                f'DELETE FROM "{V2_TABLE}" WHERE id = ?', (ref.id,)
            )
            deleted += cursor.rowcount if cursor.rowcount > 0 else 0
        conn.commit()
    finally:
        if not was_enabled:
            conn.execute("PRAGMA foreign_keys = OFF")
    return deleted


def delete_archived(conn: sqlite3.Connection) -> int:
    if not is_v2_database(conn) or "time_archived" not in _columns(conn, V2_TABLE):
        return 0
    refs = [
        SessionRef(id=str(row[0]))
        for row in conn.execute(
            f'SELECT id FROM "{V2_TABLE}" WHERE time_archived IS NOT NULL'
        )
    ]
    return delete_sessions(conn, refs)


def vacuum_database(conn: sqlite3.Connection) -> None:
    conn.commit()
    conn.execute("VACUUM")


def format_size(size_bytes: float) -> str:
    value = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024:
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} TB"
