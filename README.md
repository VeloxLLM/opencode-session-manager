# OpenCode Session Manager

> 管理 opencode 会话的 GUI/TUI 工具

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-GPL%203.0-green.svg)](LICENSE)

## AI 工作文档

本项目提供 AI 工作交接文档，方便 AI 助手快速了解项目：

| 文件 | 说明 |
|------|------|
| [ai.md](ai.md) | 中文版 AI 交接文档 |
| [ai_EN.md](ai_EN.md) | 英文版 AI 交接文档 |

## 简介

OpenCode Session Manager 是一个用于管理 [opencode](https://github.com/anomalyco/opencode) 会话数据的桌面工具。支持 GUI（图形界面）和 TUI（终端界面）两种模式，可以帮助你查看、删除、压缩和存档 opencode 的会话记录。

## 功能特性

| 功能 | 说明 |
|------|------|
| 📋 查看 | 按工作区分组显示所有会话，支持时间筛选 |
| 🗑️ 删除 | 批量选择并删除不需要的会话 |
| 🧹 清理 | 一键删除所有空会话/已归档会话 |
| 📦 压缩 | VACUUM 数据库，清理删除操作留下的空闲空间 |
| 💾 存档 | 导出会话到 JSON 文件进行备份，支持导入恢复 |
| 🗂️ 归档管理 | 管理桌面版 opencode 的归档数据 |
| 🌐 中英文 | 支持中文/英文界面切换 |
| ⏰ 时间筛选 | 按今天/7天/30天筛选会话 |

## 数据源

| 数据库 | 位置 | 说明 |
|--------|------|------|
| `opencode.db` | `~/.local/share/opencode/` | CLI/GUI 当前会话（默认） |
| `drafts.sqlite` | `%APPDATA%\ai.opencode.desktop\` | 桌面版归档数据（归档管理） |

## 系统要求

- Python 3.7 或更高版本
- tkinter（Python 内置，GUI 模式需要）

## 安装

```bash
# 克隆仓库
git clone https://github.com/VeloxLLM/opencode-session-manager.git

# 进入项目目录
cd opencode-session-manager
```

## 使用方法

```bash
python opencode_session_manager.py
```

### 功能说明

1. **会话管理**：直接管理 opencode CLI/GUI 的当前会话
2. **归档管理**：点击「归档管理」按钮，管理桌面版 opencode 的归档数据
3. **时间筛选**：使用时间下拉框筛选今天/7天/30天内的会话

或在 GUI 中点击「终端版」按钮启动。

### TUI 快捷键

| 键 | 功能 |
|---|------|
| ↑/↓ | 上下移动 |
| Enter | 查看详情 |
| d | 删除当前会话 |
| e | 删除空会话 |
| v | 压缩数据库 |
| r | 刷新 |
| q | 退出 |

### 数据库位置

程序会自动查找以下位置的 `drafts.sqlite` 文件：

| 系统 | 路径 |
|------|------|
| Windows | `%APPDATA%\ai.opencode.desktop\drafts.sqlite` |
| Windows (Local) | `%LOCALAPPDATA%\ai.opencode.desktop\drafts.sqlite` |

如果未找到，可以点击「选择数据库」按钮手动选择。

## 界面说明

### GUI 界面

```
┌─────────────────────────────────────────────────────────────┐
│  [刷新] [选择数据库] │ [删除空会话] [压缩数据库] [存档] [导入] │
├─────────────────────────────────────────────────────────────┤
│ 数据库信息: 路径/大小/记录数                                  │
├────────────────────────────┬────────────────────────────────┤
│ 会话列表                    │ 会话详情                        │
│                            │                                │
│ 📝 草稿 (45)               │ === 键 ===                     │
│   ├─ 提示词预览...          │ opencode.draft.xxx:draft:prompt│
│   └─ 提示词预览...          │                                │
│                            │ === 内容 (JSON) ===            │
│ 📁 工作区 (20)             │ {                              │
│   ├─ 提示词预览...          │   "prompt": [...]              │
│   └─ 提示词预览...          │ }                              │
│                            │                                │
│ 🌐 全局历史                 │                                │
└────────────────────────────┴────────────────────────────────┘
```

### TUI 界面

```
 OpenCode Session Manager (TUI)                Sessions: 91
    1. 给我一个 git 的名字...
    2. 用 py 写一个管理 opencode...
    3. (empty)
    4. 检测一下速度大概是多少...
    ...
───────────────────────────────────────────────────────────────
 q:Quit  d:Delete  e:DeleteEmpty  v:Vacuum  a:Archive  r:Refresh
```

## 存档格式

导出的 JSON 文件格式：

```json
{
  "version": 1,
  "created_at": "2026-09-01T21:00:00",
  "source": "path/to/drafts.sqlite",
  "records": [
    {
      "key": "session_key",
      "value": "{\"prompt\":[...]}"
    }
  ]
}
```

## 数据库结构

opencode 使用 SQLite 数据库存储会话数据：

| 表名 | 说明 |
|------|------|
| `document` | 存储会话数据（key-value 格式） |
| `blob` | 存储二进制数据 |

键名格式：
- `opencode.draft.*:draft:prompt` - 草稿
- `opencode.workspace.*.dat:session:ses_*:prompt` - 工作区会话
- `opencode.global.dat:prompt-history` - 全局历史

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

GPL 3.0 - 详见 [LICENSE](LICENSE) 文件
