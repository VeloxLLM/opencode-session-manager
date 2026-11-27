# OpenCode Session Manager

[![Rust](https://img.shields.io/badge/Rust-1.75%2B-orange.svg)](https://www.rust-lang.org/)
[![OpenCode](https://img.shields.io/badge/OpenCode-v2-4c6fff.svg)](https://github.com/anomalyco/opencode)
[![License](https://img.shields.io/badge/License-GPL--3.0-green.svg)](LICENSE)

**English** | [中文](#中文)

---

> [!NOTE]
> **Archived — no updates for now.** The tool is working reliably, so active maintenance is paused and no further updates are planned at this time.
> **已归档，暂时不再更新。** 目前工具使用正常、运行稳定，因此暂停维护，暂无更新计划。

## English

### What it does

A native desktop utility for inspecting, filtering, deleting and backing up **OpenCode v2** sessions. It reads the local SQLite database directly — no server, no API key, no telemetry.

This project is **Rust-only**. It uses only the v2 tables (`session_v2`, `session_message`, `session_part`); databases without `session_v2` are rejected.

### Features

- Session list from `session_v2`, newest first
- Filter by status (all / active / archived), time window (all / today / 7 days / 30 days) and free-text search
- Grouping by project directory; detail columns include title, version, message count, token totals and cost
- Batch delete with foreign-key cascades enabled, plus one-click deletion of all archived sessions
- Full JSON backup: session row + messages + parts, restorable into the same database
- Database VACUUM
- Chinese / English UI toggle

### Data source

| Table | Purpose |
| --- | --- |
| `session_v2` | Sessions |
| `session_message` | Assistant / user messages |
| `session_part` | Message parts |

Default location: `~/.local/share/opencode/opencode.db`. Set `OPENCODE_SESSION_MANAGER_DB` to override the path.

### Build and run

```bash
git clone https://github.com/VeloxLLM/opencode-session-manager.git
cd opencode-session-manager/rust
cargo build --release
cargo run --release
```

The binary is `rust/target/release/opencode-session-manager`.

### Backup and restore

Type or paste a file path into the **Archive path** field, then use **Export** or **Import**:

- **Export** writes the selected sessions, their messages and parts as version 2 JSON.
- **Import** accepts only version 2 archives. Duplicate session IDs are replaced.

```json
{
  "format": "opencode-session-manager",
  "version": 2,
  "sessions": [
    {
      "table": "session_v2",
      "row": { "id": "ses_...", "title": "...", "project_id": "..." },
      "messages": [],
      "parts": []
    }
  ]
}
```

### Safety

- Deletion and import write to the real OpenCode database. Back it up first and close OpenCode when possible.
- Delete operations enable `PRAGMA foreign_keys` so child rows are removed with their session.
- Import temporarily disables foreign keys, inserts a minimal `project` row when needed, then restores sessions, messages and parts.
- `VACUUM` rebuilds the whole file; it may fail while OpenCode holds a write lock.

### Layout

```text
rust/Cargo.toml
rust/src/main.rs    v2-only GUI, database access, backup and restore
```

### License

GPL-3.0. See [LICENSE](LICENSE).

---

## 中文

### 这个工具做什么

原生桌面工具，用于查看、筛选、删除和备份 **OpenCode v2** 会话。直接读取本机 SQLite 数据库，不需要服务端、API Key，也没有遥测。

本项目**只有 Rust 实现**，只使用 v2 数据表（`session_v2`、`session_message`、`session_part`）；不含 `session_v2` 的数据库会被拒绝。

### 功能

- 读取 `session_v2` 会话列表，按更新时间倒序
- 支持状态（全部 / 活跃 / 已归档）、时间（全部 / 今天 / 7 天 / 30 天）与关键词筛选
- 按项目目录分组，详情包含标题、版本、消息数、Token 与费用
- 批量删除（开启外键级联）与一键删除全部已归档会话
- 完整 JSON 备份：会话行 + 消息 + 片段，可导回同一数据库
- 数据库 VACUUM
- 中英文界面切换

### 数据源

| 数据表 | 用途 |
| --- | --- |
| `session_v2` | 会话 |
| `session_message` | 用户 / 助手消息 |
| `session_part` | 消息片段 |

默认位置：`~/.local/share/opencode/opencode.db`。可通过 `OPENCODE_SESSION_MANAGER_DB` 环境变量覆盖。

### 构建与运行

```bash
git clone https://github.com/VeloxLLM/opencode-session-manager.git
cd opencode-session-manager/rust
cargo build --release
cargo run --release
```

产物位于 `rust/target/release/opencode-session-manager`。

### 备份与恢复

在 **存档路径** 输入框中填写路径，然后点 **导出** 或 **导入**：

- **导出**：把选中会话及其消息、片段写成 version 2 JSON。
- **导入**：只接受 version 2 存档；相同 ID 的会话会被覆盖。

JSON 结构见上方英文章节。

### 安全说明

- 删除和导入会写入真实数据库，操作前请先备份并尽量关闭 OpenCode。
- 删除时启用 `PRAGMA foreign_keys`，会话子记录随之删除。
- 导入会临时关闭外键，必要时补一条最小化 `project` 行，再恢复会话、消息与片段。
- `VACUUM` 会重建整个数据库文件；OpenCode 持有写锁时可能失败。

### 目录结构

```text
rust/Cargo.toml
rust/src/main.rs    v2-only 界面、数据库访问、备份与恢复
```

### 许可证

GPL-3.0，详见 [LICENSE](LICENSE)。
