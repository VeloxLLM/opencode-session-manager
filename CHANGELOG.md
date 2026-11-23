# Changelog

## v2.0.2 — 2026-11-23 (Rust only)

- Removed the Python implementation entirely (`py/`, `tests/`); the Rust GUI is now the only implementation.
- Ported Python-only features to Rust: version 2 JSON export/import, delete-all-archived, status filter, directory grouping, session detail panel and extended search over title/directory/session ID/project ID.
- Backup path is entered in the GUI instead of using a native file dialog, avoiding extra dependencies.
- README, handoff documents and repository metadata now describe a Rust-only, OpenCode v2-only tool.

## v2.0.1 — 2026-11-23 (v2 only)

- Removed all legacy compatibility paths: `session`, `message`, `part` and `document` tables are no longer read or written.
- Core layer, tkinter GUI, Rust GUI, tests and documentation now target OpenCode v2 exclusively.
- Databases without `session_v2` are rejected with a clear message; only version 2 JSON archives are accepted.

## v2.0.0 — 2026-11-23

- Added OpenCode v2 support: reads `session_v2` / `session_message` / `session_part` alongside legacy `session` / `message` / `part`.
- Added a GUI-independent database core (`py/opencode_core.py`) with schema detection, merged listing, filtering, cascading deletes and full JSON backup/restore.
- Rebuilt the tkinter GUI with search, status/time filters, session details, v1/v2 badges and `OPENCODE_SESSION_MANAGER_DB` override.
- Added 8 headless unit tests covering both schema generations.
- Rust GUI now reads both session tables and deletes from the correct table; `Cargo.toml` bumped to 2.0.0.
- Consolidated README into one bilingual file; refreshed AI handoff documents.

## Earlier

- Added JSON archive/import, time filters and archive manager.
- Added a Rust/egui GUI; removed the TUI.
- Initial release: tkinter GUI over the legacy `drafts.sqlite` `document` table.
