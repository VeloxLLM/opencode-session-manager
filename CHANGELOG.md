# Changelog

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
