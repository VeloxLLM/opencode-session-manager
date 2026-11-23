# OpenCode Session Manager 交接

> 本文件是给 AI 的工作交接文档，请先阅读再继续操作本仓库。

## 一、还没做完的事 & 动手前注意

### 待办

- [ ] 用真实 OpenCode v2 桌面版数据库做一次 GUI 交互验收（当前环境只能跑核心层测试，无法打开窗口）
- [ ] 为 Rust 版补齐导出 / 导入功能（目前仅 Python 版支持完整备份）
- [ ] 增加按工作区的 Token / 费用汇总
- [ ] 支持深色主题

### 动手前注意

1. **本仓库仅支持 OpenCode v2**：只用 `session_v2`、`session_message`、`session_part`。不要重新引入 `session` / `message` / `document` 的兼容分支。
2. Python 核心层在 `py/opencode_core.py`，**不依赖 GUI**；改数据逻辑优先改这里，`py/tests/test_core.py` 必须继续通过。
3. 删除必须走 `core.delete_sessions()` / `core.delete_archived()`，它们会开启外键级联。
4. 导入会写真实数据库；测试只用临时 fixture，不要拿 `~/.local/share/opencode/opencode.db` 做写测试。
5. 不含 `session_v2` 的数据库会被拒绝，这是预期行为。
6. `VACUUM` 在 OpenCode 持有写锁时会失败，属于预期行为。

## 二、历史记录

### 2026-09-01

- 初始化项目，Python tkinter GUI，读取 `drafts.sqlite` 的 `document` 表。

### 2026-09-01 ~ 09-02

- 改为读取 `opencode.db` 的 `session` 表，增加归档筛选、时间筛选、JSON 存档。
- 增加 Rust/egui GUI；移除 TUI。

### 2026-11-23 — v2.0.0

- 核对本机 opencode **v2.3.0**：当前会话写入 `session_v2`，消息写入 `session_message` / `session_part`。
- 新增 `py/opencode_core.py`、重写 tkinter GUI、Rust 版支持双表读取；发布 v2.0.0 Release。

### 2026-11-23 — 仅 v2 清理

- 移除全部 v1 / legacy 代码路径：`session`、`message`、`part`、`document` 相关查询、归档管理窗口与 v1 存档导入。
- 核心层、GUI、Rust 界面、测试与全部文档统一收敛为 v2-only。

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

OpenCode v2 把会话与消息迁移到新表；本项目的价值在于提供一个安全的本地界面来查看、筛选、删除和备份这些会话。当前版本刻意不支持旧数据格式，以保持代码简单、行为可预测。

复用方式：核心层可直接被其他脚本 import；单元测试提供 v2 最小表结构 fixture，便于扩展。
