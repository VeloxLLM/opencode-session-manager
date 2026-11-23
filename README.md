# OpenCode Session Manager

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Rust](https://img.shields.io/badge/Rust-optional-orange.svg)](https://www.rust-lang.org/)
[![OpenCode](https://img.shields.io/badge/OpenCode-v2%20%7C%20v1-4c6fff.svg)](https://github.com/anomalyco/opencode)
[![License](https://img.shields.io/badge/License-GPL--3.0-green.svg)](LICENSE)

**English** | [中文](#中文)

---

## English

### What it does

A desktop utility for inspecting, filtering, deleting and backing up OpenCode sessions. It reads the local SQLite database directly — no server, no API key, no telemetry.

**Why v2.0 exists:** OpenCode 2.x moved current sessions from the `session` table to `session_v2`, and moved messages to `session_message` / `session_part`. Earlier versions of this tool only read `session`, so v2 sessions were invisible and deleting a session could leave v2 child rows behind. v2.0 reads and writes both generations and exports complete session records.

### Features

- Unified list of `session_v2` (v2) and `session` (v1) sessions, newest first
- Filter by status (all / active / archived), time window (today / 7 d / 30 d) and free-text search
- Grouping by project directory, with title, version, message count, token totals and cost in the detail pane
- Batch delete with foreign-key cascades enabled, plus one-click removal of archived sessions
- Full JSON backup: session row + messages + parts, restorable into the same database
- Legacy `drafts.sqlite` archive manager (`document` key/value records)
- Database VACUUM with before/after size reporting
- Chinese / English UI toggle
- Optional Rust/egui GUI with the same v2-aware reading and deletion logic

### Data sources

| Format | Table(s) | Typical location |
| --- | --- | --- |
| OpenCode v2 | `session_v2`, `session_message`, `session_part` | `~/.local/share/opencode/opencode.db` |
| OpenCode v1 | `session`, `message`, `part` | same `opencode.db` |
| Desktop draft archive | `document` | `%APPDATA%\ai.opencode.desktop\drafts.sqlite` |

Database discovery honours `OPENCODE_SESSION_MANAGER_DB`, `XDG_DATA_HOME`, `%LOCALAPPDATA%` and `%APPDATA%`, so custom installs can be selected without editing code.

### Run the Python GUI

```bash
git clone https://github.com/VeloxLLM/opencode-session-manager.git
cd opencode-session-manager
python py/opencode_session_manager.py
```

Requirements: Python 3.8+ with `tkinter`. No third-party packages.

A specific database can be supplied without using the file picker:

```bash
OPENCODE_SESSION_MANAGER_DB=/path/to/opencode.db python py/opencode_session_manager.py
```

### Build the Rust GUI (optional)

```bash
cd rust
cargo build --release
```

### Backup format (v2)

```json
{
  "format": "opencode-session-manager",
  "version": 2,
  "created_at": "2026-11-23T18:00:00",
  "source": "/path/to/opencode.db",
  "sessions": [
    {
      "table": "session_v2",
      "row": { "id": "ses_...", "title": "...", "project_id": "...", "cost": 0.0 },
      "messages": [{ "id": "msg_...", "type": "assistant", "seq": 1, "data": "{}" }],
      "parts": []
    }
  ]
}
```

Version 1 archives (`{"version": 1, "records": [{"key": ..., "value": ...}]}`) can still be imported.

### Safety

- Deletion and import write to the real OpenCode database. Back it up first and close OpenCode when possible.
- Delete operations enable `PRAGMA foreign_keys` so child rows are removed with their session.
- Import inserts a minimal `project` row when the referenced project is missing, then restores sessions, messages and parts in order.
- `VACUUM` rebuilds the whole file; it may fail while OpenCode holds a write lock.

### Tests and layout

```bash
python -m unittest discover -s tests -v
```

```text
py/opencode_core.py                 schema detection, query/delete/backup layer
py/opencode_session_manager.py      tkinter GUI
py/tests/test_core.py               headless unit tests (v1 + v2 fixtures)
rust/src/main.rs                    optional native GUI
```

### License

GPL-3.0. See [LICENSE](LICENSE).

---

## 中文

### 这个工具做什么

直接读取本机 SQLite 数据库，查看、筛选、删除和备份 OpenCode 会话。不需要服务端、不需要 API Key，也没有遥测。

**v2.0 的由来：** OpenCode 2.x 把当前会话从 `session` 表迁到了 `session_v2`，消息也改为存放在 `session_message` / `session_part`。旧版工具只读 `session`，因此看不到 v2 会话，删除时也可能留下 v2 子记录。v2.0 同时支持两代 schema，并导出完整会话数据。

### 功能

- 合并显示 `session_v2`（v2）与 `session`（v1）会话，按更新时间倒序
- 支持状态（全部 / 活跃 / 已归档）、时间（今天 / 7 天 / 30 天）和关键词筛选
- 按项目目录分组，详情显示标题、版本、消息数、Token 与费用
- 批量删除（开启外键级联）与一键删除已归档会话
- 完整 JSON 备份：会话行 + 消息 + 片段，可导回同一数据库
- 旧版 `drafts.sqlite` 归档管理（`document` 键值对）
- 数据库 VACUUM，并报告压缩前后体积
- 中英文界面切换
- 可选的 Rust/egui 原生界面，同样兼容 v2

### 数据源

| 格式 | 数据表 | 常见位置 |
| --- | --- | --- |
| OpenCode v2 | `session_v2`、`session_message`、`session_part` | `~/.local/share/opencode/opencode.db` |
| OpenCode v1 | `session`、`message`、`part` | 同一个 `opencode.db` |
| 桌面草稿归档 | `document` | `%APPDATA%\ai.opencode.desktop\drafts.sqlite` |

程序依次检查 `OPENCODE_SESSION_MANAGER_DB`、`XDG_DATA_HOME`、`%LOCALAPPDATA%` 与 `%APPDATA%`，自定义安装路径无需改代码。

### 运行 Python 版

```bash
git clone https://github.com/VeloxLLM/opencode-session-manager.git
cd opencode-session-manager
python py/opencode_session_manager.py
```

要求：Python 3.8+ 且带 `tkinter`，无第三方依赖。

也可以跳过文件选择框，直接指定数据库：

```bash
OPENCODE_SESSION_MANAGER_DB=/path/to/opencode.db python py/opencode_session_manager.py
```

### 构建 Rust 版（可选）

```bash
cd rust
cargo build --release
```

### v2 备份格式

见上方英文章节的 JSON 示例。v1 格式（`{"version": 1, "records": [...]}`）仍可导入。

### 安全说明

- 删除和导入会写入真实的 OpenCode 数据库，操作前请先备份，并尽量关闭 OpenCode。
- 删除时启用 `PRAGMA foreign_keys`，会话子记录会随之删除。
- 导入时若项目记录缺失，会补一条最小化的 `project` 行，再按顺序恢复会话、消息和片段。
- `VACUUM` 会重建整个数据库文件；OpenCode 持有写锁时可能失败。

### 测试与目录结构

```bash
python -m unittest discover -s tests -v
```

```text
py/opencode_core.py                 数据库核心层（schema 检测、查询、删除、备份）
py/opencode_session_manager.py      tkinter 图形界面
py/tests/test_core.py               无界面单元测试（v1 + v2 测试数据）
rust/src/main.rs                    可选的原生界面
```

### 许可证

GPL-3.0，详见 [LICENSE](LICENSE)。
