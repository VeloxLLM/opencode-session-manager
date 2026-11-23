# OpenCode Session Manager Handoff

> Read this file before continuing work on this repository.

## 1. Pending work & precautions

### TODO

- [ ] Run an interactive GUI acceptance test against a real OpenCode v2 desktop database (this environment can only run headless core tests)
- [ ] Port full export/import to the Rust GUI (currently Python only)
- [ ] Add per-workspace token / cost aggregation
- [ ] Add a dark theme

### Precautions

1. **This repository supports OpenCode v2 only**: `session_v2`, `session_message`, `session_part`. Do not reintroduce `session` / `message` / `document` compatibility paths.
2. The Python data layer is `py/opencode_core.py` and is GUI-independent. Change data logic there and keep `py/tests/test_core.py` green.
3. Always delete through `core.delete_sessions()` / `core.delete_archived()` — they enable foreign-key cascades.
4. Import writes to the real database. Use temporary fixtures for tests, never `~/.local/share/opencode/opencode.db`.
5. A database without `session_v2` is rejected by design.
6. `VACUUM` can fail while OpenCode holds a write lock; that is expected.

## 2. History

### 2026-09-01

- Initial Python tkinter GUI reading `document` rows from `drafts.sqlite`.

### 2026-09-01 to 09-02

- Switched to `session` in `opencode.db`; added filters and JSON archive.
- Added a Rust/egui GUI and removed the TUI.

### 2026-11-23 — v2.0.0

- Verified local opencode **v2.3.0**: current sessions are written to `session_v2`, messages to `session_message` / `session_part`.
- Added `py/opencode_core.py`, rewrote the tkinter GUI, updated the Rust GUI to read both generations, and published v2.0.0.

### 2026-11-23 — v2-only cleanup

- Removed all v1 / legacy paths: `session`, `message`, `part`, `document` queries, the legacy archive window and v1 archive import.
- Core layer, both GUIs, tests and all documentation are now v2-only.

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

OpenCode v2 moved sessions and messages to new tables. This project provides a safe local UI to inspect, filter, delete and back them up. The current version intentionally does not support older data formats, keeping the code simple and behaviour predictable.

Reuse: the core layer can be imported by other scripts; the unit tests provide minimal v2 schema fixtures for further work.
