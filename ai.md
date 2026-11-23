# OpenCode Session Manager 交接

> 本文件是给 AI 的工作交接文档，请先阅读再继续操作本仓库。

## 一、还没做完的事 & 动手前注意

### 待办

- [ ] 用真实 OpenCode v2 桌面版数据库做一次 GUI 交互验收（当前环境无法启动窗口）
- [ ] 增加按工作区的 Token / 费用汇总
- [ ] 支持深色主题
- [x] `cargo check --offline` 与 `cargo build --release --offline` 已在本机通过（零警告）

### 动手前注意

1. **本仓库只有 Rust 实现**：唯一源码为 `rust/src/main.rs`。不要再引入 Python 或 GUI 之外的第二套实现。
2. **仅支持 OpenCode v2**：只用 `session_v2`、`session_message`、`session_part`。不要重新引入 `session` / `message` / `document` 兼容分支。
3. 删除固定从 `session_v2` 执行，并开启 `PRAGMA foreign_keys` 级联删除子记录。
4. 导入只接受 version 2 JSON，会临时关闭外键、补最小 `project` 行，再恢复会话 / 消息 / 片段。
5. 备份路径由界面上的「存档路径」输入框指定，无文件选择对话框；这是为了避免引入额外依赖。
6. `VACUUM` 在 OpenCode 持有写锁时会失败，属于预期行为。

## 二、历史记录

### 2026-09-01 ~ 09-02

- 早期 Python/tkinter 版本，先后读取 `drafts.sqlite` 与 `opencode.db` 的旧表；已全部删除。

### 2026-11-23 — v2.0.0

- 核对本机 opencode **v2.3.0**：当前会话写入 `session_v2`，消息写入 `session_message` / `session_part`。
- 发布 v2.0.0，加入 v2 数据读取、筛选、删除与双语 README。

### 2026-11-23 — v2-only 清理

- 移除全部 v1 / legacy 代码路径与文档描述。

### 2026-11-23 — Rust-only

- 删除 `py/` 与 `tests/` 目录，彻底移除 Python 实现。
- 将 Python 独有的 **JSON 导出 / 导入**、**删除已归档**、**状态筛选**、**目录分组**、**会话详情面板**以及按标题 / 目录 / 会话 ID / 项目 ID 搜索移植到 Rust GUI。
- README / 交接文档 / CHANGELOG 改为 Rust-only；GitHub Topics 移除 python / tkinter。

当前目录：

```text
opencode-session-manager/
├── README.md                 README_EN.md                 CHANGELOG.md
├── LICENSE
└── rust/
    ├── Cargo.toml            src/main.rs
```

## 三、为什么做这件事

OpenCode v2 把会话与消息迁移到新表；本项目的价值在于提供一个安全的本地界面来查看、筛选、删除和备份这些会话。当前版本只有单一 Rust 实现，避免双实现带来的行为漂移与维护成本。

复用方式：`rust/src/main.rs` 中的 SQL 与备份格式定义可直接参考或抽取为独立 crate。
