# OpenCode Session Manager

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Rust](https://img.shields.io/badge/Rust-optional-orange.svg)](https://www.rust-lang.org/)
[![OpenCode](https://img.shields.io/badge/OpenCode-v2-4c6fff.svg)](https://github.com/anomalyco/opencode)
[![License](https://img.shields.io/badge/License-GPL--3.0-green.svg)](LICENSE)

**English** | [中文](#中文)

---

## English

### What it does

A desktop utility for inspecting, filtering, deleting and backing up **OpenCode v2** sessions. It reads the local SQLite database directly — no server, no API key, no telemetry.

Scope is deliberately narrow: only the v2 tables (`session_v2`, `session_message`, `session_part`) are used. Databases without `session_v2` are rejected with a clear message.

### Features

- Session list from `session_v2`, newest first
- Filter by status (all / active / archived), time window (today / 7 d / 30 d) and free-text search
- Grouping by project directory, with title, version, message count, token totals and cost in the detail pane
- Batch delete with foreign-key cascades enabled, plus one-click removal of archived sessions
- Full JSON backup: session row + messages + parts, restorable into the same database
- Database VACUUM with before/after size reporting
- Chinese / English UI toggle
- Optional Rust/egui GUI with the same v2-only logic

### Data source

| Table | Purpose |
| --- | --- |
| `session_v2` | Sessions |
| `session_message` | Assistant / user messages |
| `session_part` | Message parts |

Default location: `~/.local/share/opencode/opencode.db`.

Discovery honours `OPENCODE_SESSION_MANAGER_DB`, `XDG_DATA_HOME`, `%LOCALAPPDATA%` and `%APPDATA%`, so custom installs can be selected without editing code.

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

### Backup format

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

Only version 2 archives are accepted.

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
py/opencode_core.py                 v2-only database layer
py/opencode_session_manager.py      tkinter GUI
py/tests/test_core.py               headless unit tests with v2 fixtures
rust/src/main.rs                    optional native GUI
```

### License

GPL-3.0. See [LICENSE](LICENSE).

---

## 中文

### 这个工具做什么

直接读取本机 SQLite 数据库，查看、筛选、删除和备份 **OpenCode v2** 会话。不需要服务端、不需要 API Key，也没有遥测。

范围刻意收窄：只使用 v2 数据表（`session_v2`、`session_message`、`session_part`）。不含 `session_v2` 的数据库会被明确拒绝。

### 功能

- 读取 `session_v2` 会话列表，按更新时间倒序
- 支持状态（全部 / 活跃 / 已归档）、时间（今天 / 7 天 / 30 天）和关键词筛选
- 按项目目录分组，详情显示标题、版本、消息数、Token 与费用
- 批量删除（开启外键级联）与一键删除已归档会话
- 完整 JSON 备份：会话行 + 消息 + 片段，可导回同一数据库
- 数据库 VACUUM，并报告压缩前后体积
- 中英文界面切换
- 可选的 Rust/egui 原生界面，逻辑同样仅限 v2

### 数据源

| 数据表 | 用途 |
| --- | --- |
| `session_v2` | 会话 |
| `session_message` | 用户 / 助手消息 |
| `session_part` | 消息片段 |

默认位置：`~/.local/share/opencode/opencode.db`。

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

### 备份格式

见上方英文章节的 JSON 示例。只接受 version 2 的存档。

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
py/opencode_core.py                 仅限 v2 的数据库核心层
py/opencode_session_manager.py      tkinter 图形界面
py/tests/test_core.py               无界面单元测试（v2 测试数据）
rust/src/main.rs                    可选的原生界面
```

### 许可证

GPL-3.0，详见 [LICENSE](LICENSE)。
