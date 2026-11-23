"""Headless tests for the v2-only database layer (no GUI, no real OpenCode data)."""

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "py"))

import opencode_core as core  # noqa: E402


V2_SCHEMA = """
CREATE TABLE project (
  id TEXT PRIMARY KEY, worktree TEXT NOT NULL, vcs TEXT, name TEXT,
  time_created INTEGER NOT NULL, time_updated INTEGER NOT NULL, sandboxes TEXT NOT NULL
);
CREATE TABLE session_v2 (
  id TEXT PRIMARY KEY, project_id TEXT NOT NULL, slug TEXT NOT NULL,
  directory TEXT NOT NULL, title TEXT NOT NULL, version TEXT NOT NULL,
  time_created INTEGER NOT NULL, time_updated INTEGER NOT NULL,
  time_archived INTEGER, cost REAL DEFAULT 0, tokens_input INTEGER DEFAULT 0,
  tokens_output INTEGER DEFAULT 0
);
CREATE TABLE session_message (
  id TEXT PRIMARY KEY, session_id TEXT NOT NULL, type TEXT NOT NULL, seq INTEGER NOT NULL,
  time_created INTEGER NOT NULL, time_updated INTEGER NOT NULL, data TEXT NOT NULL,
  FOREIGN KEY (session_id) REFERENCES session_v2(id) ON DELETE CASCADE
);
CREATE TABLE session_part (
  message_id TEXT NOT NULL, session_id TEXT NOT NULL, ordinal INTEGER NOT NULL,
  type TEXT NOT NULL, time_created INTEGER NOT NULL, time_updated INTEGER NOT NULL,
  data TEXT NOT NULL, PRIMARY KEY (message_id, ordinal),
  FOREIGN KEY (session_id) REFERENCES session_v2(id) ON DELETE CASCADE
);
"""


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "opencode.db"
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(V2_SCHEMA)
        self.conn.execute(
            "INSERT INTO project VALUES ('p1', '/work', NULL, NULL, 1, 1, '[]')"
        )
        now = core._now_ms()
        self.conn.execute(
            "INSERT INTO session_v2 VALUES ('v2-a','p1','v2-a','/work','v2 alpha','2.3.0',?,?,NULL,1.5,100,20)",
            (now - 1000, now),
        )
        self.conn.execute(
            "INSERT INTO session_v2 VALUES ('v2-b','p1','v2-b','/work','v2 old','2.3.0',?,?,?,0,0,0)",
            (now - 86400000 * 40, now - 86400000 * 40, now - 86400000 * 40),
        )
        self.conn.execute(
            "INSERT INTO session_message VALUES ('m1','v2-a','assistant',1,?,?,'{\"cost\":1}')",
            (now, now),
        )
        self.conn.execute(
            "INSERT INTO session_part VALUES ('m1','v2-a',0,'text',?,?,'{}')", (now, now)
        )
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        self.temp.cleanup()

    def test_schema_detection(self):
        self.assertTrue(core.is_v2_database(self.conn))
        self.assertTrue(core.detect_schema(self.conn)["v2"])

    def test_lists_sessions(self):
        sessions = core.list_sessions(self.conn)
        self.assertEqual([item.ref.id for item in sessions], ["v2-a", "v2-b"])
        self.assertEqual(sessions[0].message_count, 1)
        self.assertEqual(sessions[0].tokens_total, 120)

    def test_filters(self):
        active = core.list_sessions(self.conn, status="active")
        archived = core.list_sessions(self.conn, status="archived")
        self.assertEqual({item.ref.id for item in active}, {"v2-a"})
        self.assertEqual({item.ref.id for item in archived}, {"v2-b"})
        self.assertEqual(len(core.list_sessions(self.conn, time_range="7d")), 1)
        self.assertEqual(len(core.list_sessions(self.conn, search="v2 old")), 1)

    def test_export_import_roundtrip(self):
        refs = [core.SessionRef.parse("session_v2:v2-a")]
        payload = core.export_sessions(self.conn, refs)
        self.assertEqual(payload["version"], 2)
        self.assertEqual(payload["sessions"][0]["table"], core.V2_TABLE)
        self.assertEqual(len(payload["sessions"][0]["messages"]), 1)
        core.delete_sessions(self.conn, refs)
        self.assertEqual([item.ref.id for item in core.list_sessions(self.conn)], ["v2-b"])
        result = core.import_archive(self.conn, payload)
        self.assertEqual(result["sessions"], 1)
        self.assertEqual(result["messages"], 1)
        self.assertEqual(result["parts"], 1)
        self.assertEqual(len(core.list_sessions(self.conn)), 2)

    def test_delete_cascades(self):
        core.delete_sessions(self.conn, [core.SessionRef.parse("session_v2:v2-a")])
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM session_message").fetchone()[0], 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM session_part").fetchone()[0], 0)

    def test_delete_archived(self):
        self.assertEqual(core.delete_archived(self.conn), 1)
        self.assertEqual([item.ref.id for item in core.list_sessions(self.conn)], ["v2-a"])

    def test_summary_and_paths(self):
        summary = core.get_database_summary(self.conn, self.path)
        self.assertEqual(summary["sessions"], 2)
        self.assertEqual(summary["archived"], 1)
        self.assertGreater(summary["size_bytes"], 0)
        os.environ["OPENCODE_SESSION_MANAGER_DB"] = str(self.path)
        try:
            self.assertEqual(core.candidate_database_paths()[0], self.path)
        finally:
            del os.environ["OPENCODE_SESSION_MANAGER_DB"]

    def test_non_v2_database_rejected(self):
        path = Path(self.temp.name) / "legacy.db"
        conn = sqlite3.connect(str(path))
        conn.execute("CREATE TABLE document (key TEXT PRIMARY KEY, value TEXT)")
        conn.commit()
        self.assertFalse(core.is_v2_database(conn))
        self.assertEqual(core.list_sessions(conn), [])
        with self.assertRaises(ValueError):
            core.import_archive(conn, {"version": 2, "sessions": []})
        conn.close()


if __name__ == "__main__":
    unittest.main()
