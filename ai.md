# OpenCode Session Manager 交接

> 本文件是给 AI 的工作交接文档，请先阅读再继续操作本仓库。

## 一、还没做完的事 & 动手前注意

### 待办

- [ ] 用真实 OpenCode v2 桌面版数据库做一次 GUI 交互验收（当前环境只能跑核心层测试，无法打开窗口）
- [ ] 为 Rust 版补齐导出 / 导入功能（目前仅 Python 版支持完整备份）
- [ ] 增加按工作区的 Token / 费用汇总
- [ ] 支持深色主题

### 动手前注意

1. Python 核心层在 `py/opencode_core.py`，**不依赖 GUI**；改数据逻辑优先改这里，`py/tests/test_core.py` 必须继续通过。
2. v2 当前会话在 `session_v2`，消息在 `session_message` / `session_part`；v1 历史在 `session` / `message` / `part`。两代数据同时展示，不要只读一张表。
3. 删除必须走 `core.delete_sessions()` / `core.delete_archived()`，它们会开启外键级联；不要手写 `DELETE FROM session`。
4. 导入会写真实数据库；测试只用临时 fixture，不要拿 `~/.local/share/opencode/opencode.db` 做写测试。
5. `VACUUM` 在 OpenCode 持有写锁时会失败，属于预期行为。
6. Rust 版 `rust/src/main.rs` 目前支持 v2/v1 读取与删除，但导出/导入尚未实现。

## 二、历史记录

### 2026-09-01

- 初始化项目，Python tkinter GUI，读取 `drafts.sqlite` 的 `document` 表。
- 建立 README / AI 交接文档。

### 2026-09-01 ~ 09-02

- 改为读取 `opencode.db` 的 `session` 表，增加归档筛选、时间筛选、JSON 存档。
- 增加 Rust/egui GUI；移除 TUI（README 曾残留 TUI 描述，v2.0 已清理）。

### 2026-11-23 — v2.0.0

- 核对本机 opencode **v2.3.0**：当前会话写入 `session_v2`，消息写入 `session_message` / `session_part`；旧 `session` 表仍有 56 条历史记录，`session_v2` 有 49 条。旧代码只读取 `session`，v2 会话完全不可见。
- 新增 `py/opencode_core.py`：schema 自动检测、v1+v2 合并列表、筛选、外键级联删除、完整 JSON 导出/导入（含 messages/parts）、旧 `document` 归档管理。
- 重写 `py/opencode_session_manager.py`：使用核心层，新增搜索、状态/时间筛选、详情面板、v1/v2 标识、中英文切换；支持 `OPENCODE_SESSION_MANAGER_DB` 环境变量。
- 新增 `tests/test_core.py`，8 项无界面单元测试全部通过。
- Rust 版同步支持 `session_v2` + `session` 双表读取与按表删除，Cargo 版本改为 2.0.0。
- README 合并为中英双语单文件；README_EN.md 保留为入口页；新增 CHANGELOG.md 与 .gitignore。

当前目录：

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

## 三、为什么做这件事

OpenCode 本身不提供会话清理界面。v2 引入新表后，旧工具会漏掉当前会话；本项目的价值在于**跨 schema 统一视图**与安全删除/备份能力，而不是替代 OpenCode 的会话功能。

复用方式：核心层可直接被其他脚本 import；单元测试提供了 v1/v2 的最小表结构 fixture，便于扩展。
