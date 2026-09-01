# OpenCode Session Manager

> 管理 opencode 会话的 GUI 工具

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 简介

OpenCode Session Manager 是一个用于管理 [opencode](https://github.com/anomalyco/opencode) 会话数据的桌面 GUI 工具。它可以帮助你查看、删除、压缩和存档 opencode 的会话记录。

## 功能特性

| 功能 | 说明 |
|------|------|
| 📋 查看 | 按工作区分组显示所有会话和草稿，支持预览提示词内容 |
| 🗑️ 删除 | 批量选择并删除不需要的会话或草稿 |
| 📦 压缩 | VACUUM 数据库，清理删除操作留下的空闲空间 |
| 💾 存档 | 导出会话到 JSON 文件进行备份，支持导入恢复 |

## 系统要求

- Python 3.7 或更高版本
- tkinter（Python 内置，无需额外安装）

## 安装

```bash
# 克隆仓库
git clone https://github.com/your-username/opencode-session-manager.git

# 进入项目目录
cd opencode-session-manager
```

## 使用方法

```bash
python opencode_session_manager.py
```

### 数据库位置

程序会自动查找以下位置的 `drafts.sqlite` 文件：

| 系统 | 路径 |
|------|------|
| Windows | `%APPDATA%\ai.opencode.desktop\drafts.sqlite` |
| Windows (Local) | `%LOCALAPPDATA%\ai.opencode.desktop\drafts.sqlite` |

如果未找到，可以点击「选择数据库」按钮手动选择。

## 界面说明

```
┌─────────────────────────────────────────────────────────────┐
│  [刷新] [选择数据库] │ [压缩数据库] [存档选中] [导入存档]    │
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

## 开发

```bash
# 运行程序
python opencode_session_manager.py
```

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件
