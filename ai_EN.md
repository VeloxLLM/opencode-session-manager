# OpenCode Session Manager Handoff

> Read this file before continuing work on this repository.

## 1. Pending work & precautions

### TODO

- [ ] Run an interactive GUI acceptance test against a real OpenCode v2 desktop database (this environment can only run headless core tests)
- [ ] Port full export/import to the Rust GUI (currently Python only)
- [ ] Add per-workspace token / cost aggregation
- [ ] Add a dark theme

### Precautions

1. The Python data layer is `py/opencode_core.py` and is GUI-independent. Change data logic there and keep `py/tests/test_core.py` green.
2. v2 current sessions live in `session_v2`, messages in `session_message` / `session_part`; v1 history stays in `session` / `message` / `part`. Show both generations.
3. Always delete through `core.delete_sessions()` / `core.delete_archived()` — they enable foreign-key cascades. Do not hand-write `DELETE FROM session`.
4. Import writes to the real database. Use temporary fixtures for tests, never `~/.local/share/opencode/opencode.db`.
5. `VACUUM` can fail while OpenCode holds a write lock; that is expected.
6. The Rust GUI reads/deletes both v2 and v1 tables, but does not yet support export/import.

## 2. History

### 2026-09-01

- Initial Python tkinter GUI reading `document` rows from `drafts.sqlite`.

### 2026-09-01 to 09-02

- Switched to `session` in `opencode.db`; added filters and JSON archive.
- Added a Rust/egui GUI and removed the TUI (stale TUI docs were cleaned up in v2.0).

### 2026-11-23 — v2.0.0

- Verified local opencode **v2.3.0**: current sessions go to `session_v2`, messages to `session_message` / `session_part`; the legacy `session` table still holds 56 historical rows versus 49 in `session_v2`. The old tool only read `session`, so v2 sessions were invisible.
- Added `py/opencode_core.py`: schema detection, merged v1+v2 listing, filtering, cascading deletes, full JSON export/import (including messages and parts), legacy `document` archive management.
- Rewrote `py/opencode_session_manager.py` to use the core layer, with search, status/time filters, detail pane, v1/v2 badges, bilingual UI and `OPENCODE_SESSION_MANAGER_DB` support.
- Added `tests/test_core.py`: 8 headless unit tests, all passing.
- Rust GUI also reads both tables and deletes from the correct table; Cargo version set to 2.0.0.
- README consolidated into one bilingual file; `README_EN.md` kept as an entry point; added `CHANGELOG.md` and `.gitignore`.

Current layout:

```text
opencode-session-manager/
├── README.md                 README_EN.md                 CHANGELOG.md
├── LICENSE
├── py/
│   ├── opencode_core.py      opencode_session_manager.py
│   └── tests/test_core.py
└── rust/
    ├── Cargo.toml            src/main.rs
```

## 3. Why this exists

OpenCode has no built-in session cleanup UI. v2 introduced new tables that made the old tool miss current sessions. This project provides a **cross-schema unified view** with safe deletion and backup, rather than replacing OpenCode's own session features.

Reuse: the core layer can be imported by other scripts; the unit tests provide minimal v1/v2 schema fixtures for further work.
