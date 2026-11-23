"""Database layer for OpenCode Session Manager.

This module is GUI-independent and supports all three data formats produced by
OpenCode over time:

* ``session_v2``  - OpenCode v2.x current sessions (``opencode.db``)
* ``session``     - OpenCode v1.x sessions (same database, kept for history)
* ``document``    - legacy desktop ``drafts.sqlite`` key/value records

Only table names from a fixed whitelist are ever interpolated into SQL. All
values are passed as parameters.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

V2_TABLE = "session_v2"
V1_TABLE = "session"
LEGACY_TABLE = "document"
SESSION_TABLES: Tuple[str, ...] = (V2_TABLE, V1_TABLE)
SESSION_TABLE_SET: Set[str] = set(SESSION_TABLES)
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
    """Unique reference to a session row (table + primary key)."""

    table: str
    id: str

    @property
    def key(self) -> str:
        return f"{self.table}:{self.id}"

    @classmethod
    def parse(cls, key: str) -> "SessionRef":
        table, sep, sid = str(key).partition(":")
        if not sep or table not in SESSION_TABLE_SET or not sid:
            raise ValueError(f"Invalid session reference: {key!r}")
        return cls(table=table, id=sid)


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
    """Return likely OpenCode database paths, most specific first."""
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


def candidate_archive_paths() -> List[Path]:
    candidates = [
        Path(os.environ.get("APPDATA", "")) / "ai.opencode.desktop" / "drafts.sqlite",
        Path(os.environ.get("LOCALAPPDATA", "")) / "ai.opencode.desktop" / "drafts.sqlite",
        Path.home() / ".local" / "share" / "ai.opencode.desktop" / "drafts.sqlite",
    ]
    seen: Set[str] = set()
    result: List[Path] = []
    for path in candidates:
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            result.append(path)
    return result


def find_archive_database() -> Optional[Path]:
    for path in candidate_archive_paths():
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


def detect_schema(conn: sqlite3.Connection) -> Dict[str, Any]:
    names = table_names(conn)
    return {
        "v2": V2_TABLE in names,
        "v1": V1_TABLE in names,
        "legacy": LEGACY_TABLE in names,
        "tables": sorted(names),
    }


def _columns(conn: sqlite3.Connection, table: str) -> Set[str]:
    if table not in table_names(conn):
        return set()
    return {row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')}


def _message_table(table: str) -> str:
    return "session_message" if table == V2_TABLE else "message"


def _part_table(table: str) -> str:
    return "session_part" if table == V2_TABLE else "part"


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
    """Return sessions from both v2 and v1 tables, newest first."""
    names = table_names(conn)
    threshold = _time_threshold_ms(time_range)
    needle = search.strip().lower()
    result: List[SessionInfo] = []

    for table in SESSION_TABLES:
        if table not in names:
            continue
        available = _columns(conn, table)
        selected = [column for column in _SESSION_COLUMNS if column in available]
        if "id" not in selected:
            continue
        sql = f'SELECT {", ".join(selected)} FROM "{table}"'
        try:
            rows = conn.execute(sql).fetchall()
        except sqlite3.Error:
            continue

        msg_table = _message_table(table)
        has_msg_table = msg_table in names
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
            if needle and needle not in " ".join((title, directory, sid, str(data.get("project_id") or ""))).lower():
                continue

            count = 0
            if has_msg_table:
                try:
                    count = conn.execute(
                        f'SELECT COUNT(*) FROM "{msg_table}" WHERE session_id = ?', (sid,)
                    ).fetchone()[0]
                except sqlite3.Error:
                    count = 0

            result.append(
                SessionInfo(
                    ref=SessionRef(table=table, id=sid),
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
    counts: Dict[str, int] = {}
    for table in SESSION_TABLES:
        if table in names:
            counts[table] = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        else:
            counts[table] = 0
    if LEGACY_TABLE in names:
        counts[LEGACY_TABLE] = conn.execute('SELECT COUNT(*) FROM "document"').fetchone()[0]
    else:
        counts[LEGACY_TABLE] = 0

    archived = 0
    for table in SESSION_TABLES:
        if table in names and "time_archived" in _columns(conn, table):
            archived += conn.execute(
                f'SELECT COUNT(*) FROM "{table}" WHERE time_archived IS NOT NULL'
            ).fetchone()[0]

    try:
        size = Path(path).stat().st_size
    except OSError:
        size = 0
    return {
        "path": str(path),
        "size_bytes": size,
        "counts": counts,
        "archived": archived,
        "schema": detect_schema(conn),
    }


def export_sessions(conn: sqlite3.Connection, refs: Sequence[SessionRef]) -> Dict[str, Any]:
    """Export complete session rows with their messages and parts."""
    names = table_names(conn)
    payload: Dict[str, Any] = {
        "format": ARCHIVE_FORMAT,
        "version": ARCHIVE_VERSION,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "source": "",
        "sessions": [],
    }
    for ref in refs:
        if ref.table not in SESSION_TABLE_SET or ref.table not in names:
            continue
        row = conn.execute(
            f'SELECT * FROM "{ref.table}" WHERE id = ?', (ref.id,)
        ).fetchone()
        if row is None:
            continue
        item: Dict[str, Any] = {"table": ref.table, "row": dict(row), "messages": [], "parts": []}
        msg_table = _message_table(ref.table)
        part_table = _part_table(ref.table)
        if msg_table in names:
            order_column = "seq" if "seq" in _columns(conn, msg_table) else "time_created"
            item["messages"] = [
                dict(message)
                for message in conn.execute(
                    f'SELECT * FROM "{msg_table}" WHERE session_id = ? ORDER BY "{order_column}"',
                    (ref.id,),
                )
            ]
        if part_table in names:
            item["parts"] = [
                dict(part)
                for part in conn.execute(
                    f'SELECT * FROM "{part_table}" WHERE session_id = ?', (ref.id,)
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
    if table not in allowed_tables:
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
    """Import a v1 (document) or v2 (full session) archive."""
    result = {"sessions": 0, "messages": 0, "parts": 0, "records": 0}
    if not isinstance(payload, dict):
        raise ValueError("Archive root must be an object")

    version = payload.get("version", 1)
    names = table_names(conn)

    if version == 1 and isinstance(payload.get("records"), list):
        for record in payload["records"]:
            if not isinstance(record, dict) or "key" not in record or "value" not in record:
                continue
            result["records"] += _insert_row(
                conn, LEGACY_TABLE, record, {LEGACY_TABLE}
            )
        conn.commit()
        return result

    if version < 2 or not isinstance(payload.get("sessions"), list):
        raise ValueError("Unsupported archive format")

    was_enabled = bool(conn.execute("PRAGMA foreign_keys").fetchone()[0])
    conn.commit()
    if was_enabled:
        conn.execute("PRAGMA foreign_keys = OFF")

    try:
        for item in payload["sessions"]:
            if not isinstance(item, dict):
                continue
            table = item.get("table")
            row = item.get("row")
            if table not in SESSION_TABLE_SET or not isinstance(row, dict):
                continue
            if table not in names:
                continue

            project_id = row.get("project_id")
            project_columns = _columns(conn, "project")
            if project_id and "project" in names and project_columns:
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

            result["sessions"] += _insert_row(conn, table, row, SESSION_TABLE_SET)
            sid = str(row.get("id") or "")
            for message in item.get("messages", []):
                if isinstance(message, dict):
                    result["messages"] += _insert_row(
                        conn, _message_table(table), message, {"message", "session_message"}
                    )
            for part in item.get("parts", []):
                if isinstance(part, dict):
                    result["parts"] += _insert_row(
                        conn, _part_table(table), part, {"part", "session_part"}
                    )
        conn.commit()
    finally:
        if was_enabled:
            conn.execute("PRAGMA foreign_keys = ON")
    return result


def delete_sessions(conn: sqlite3.Connection, refs: Sequence[SessionRef]) -> int:
    """Delete sessions from their own tables with foreign keys enforced."""
    names = table_names(conn)
    valid = [ref for ref in refs if ref.table in SESSION_TABLE_SET and ref.table in names]
    if not valid:
        return 0
    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON")
    deleted = 0
    try:
        for ref in valid:
            cursor = conn.execute(
                f'DELETE FROM "{ref.table}" WHERE id = ?', (ref.id,)
            )
            deleted += cursor.rowcount if cursor.rowcount > 0 else 0
        conn.commit()
    finally:
        conn.execute("PRAGMA foreign_keys = OFF")
    return deleted


def delete_archived(conn: sqlite3.Connection) -> int:
    names = table_names(conn)
    refs: List[SessionRef] = []
    for table in SESSION_TABLES:
        if table not in names or "time_archived" not in _columns(conn, table):
            continue
        for row in conn.execute(
            f'SELECT id FROM "{table}" WHERE time_archived IS NOT NULL'
        ):
            refs.append(SessionRef(table=table, id=str(row[0])))
    return delete_sessions(conn, refs)


def list_legacy_records(conn: sqlite3.Connection) -> List[Tuple[str, str]]:
    if LEGACY_TABLE not in table_names(conn):
        return []
    return [
        (str(row[0]), str(row[1]))
        for row in conn.execute('SELECT key, value FROM "document" ORDER BY key')
    ]


def delete_legacy_records(conn: sqlite3.Connection, keys: Iterable[str]) -> int:
    keys = list(keys)
    if not keys or LEGACY_TABLE not in table_names(conn):
        return 0
    placeholders = ", ".join("?" for _ in keys)
    cursor = conn.execute(
        f'DELETE FROM "document" WHERE key IN ({placeholders})', keys
    )
    conn.commit()
    return cursor.rowcount if cursor.rowcount > 0 else 0


def vacuum_database(conn: sqlite3.Connection) -> None:
    conn.commit()
    conn.execute("VACUUM")


def extract_preview(value: str, limit: int = 50) -> str:
    """Extract the first non-empty prompt text from a legacy draft value."""
    try:
        data = json.loads(value)
        prompt = data.get("prompt") if isinstance(data, dict) else None
        if isinstance(prompt, list):
            for part in prompt:
                if isinstance(part, dict):
                    content = part.get("content")
                    if isinstance(content, str) and content.strip():
                        return content[:limit] + ("..." if len(content) > limit else "")
        return ""
    except (ValueError, TypeError):
        return ""


def format_size(size_bytes: float) -> str:
    value = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024:
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} TB"
