# OpenCode Session Manager Handoff

> Read this file before continuing work on this repository.

## 1. Pending work & precautions

### TODO

- [ ] Run an interactive GUI acceptance test against a real OpenCode v2 database (windows cannot be opened in this environment)
- [ ] Add per-workspace token / cost aggregation
- [ ] Add a dark theme
- [x] `cargo check --offline` and `cargo build --release --offline` pass locally with zero warnings

### Precautions

1. **This repository has a single Rust implementation**: the only source file is `rust/src/main.rs`. Do not reintroduce Python or a second implementation.
2. **OpenCode v2 only**: `session_v2`, `session_message`, `session_part`. Do not reintroduce `session` / `message` / `document` compatibility paths.
3. Deletion always targets `session_v2` with `PRAGMA foreign_keys` enabled so child rows are removed.
4. Import accepts only version 2 JSON. It temporarily disables foreign keys, inserts a minimal `project` row when needed, then restores sessions / messages / parts.
5. The archive path comes from the on-screen **Archive path** text field — there is no file dialog, to avoid extra dependencies.
6. `VACUUM` can fail while OpenCode holds a write lock; that is expected.

## 2. History

### 2026-09-01 to 09-02

- Early Python/tkinter versions reading `drafts.sqlite` and then legacy `opencode.db` tables; all removed.

### 2026-11-23 — v2.0.0

- Verified local opencode **v2.3.0**: sessions go to `session_v2`, messages to `session_message` / `session_part`.
- Published v2.0.0 with v2 reading, filtering, deletion and a bilingual README.

### 2026-11-23 — v2-only cleanup

- Removed all v1 / legacy code paths and documentation references.

### 2026-11-23 — Rust-only

- Deleted `py/` and `tests/`; removed the Python implementation entirely.
- Ported Python-only **JSON export/import**, **delete archived**, **status filter**, **directory grouping**, **session details panel** and search over title / directory / session ID / project ID into the Rust GUI.
- README, handoff docs and changelog are now Rust-only; GitHub topics dropped python / tkinter.

Current layout:

```text
opencode-session-manager/
├── README.md                 README_EN.md                 CHANGELOG.md
├── LICENSE
└── rust/
    ├── Cargo.toml            src/main.rs
```

## 3. Why this exists

OpenCode v2 moved sessions and messages to new tables. This project provides a safe local UI to inspect, filter, delete and back them up. A single Rust implementation avoids behaviour drift and maintenance cost from having two implementations.

Reuse: the SQL and backup format in `rust/src/main.rs` can be referenced or extracted into a crate.
