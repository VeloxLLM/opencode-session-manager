# OpenCode Session Manager

> A GUI/TUI tool for managing opencode sessions

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-GPL%203.0-green.svg)](LICENSE)

## AI Documentation

This project provides AI handoff documents for quick onboarding:

| File | Description |
|------|-------------|
| [ai.md](ai.md) | AI handoff document (Chinese) |
| [ai_EN.md](ai_EN.md) | AI handoff document (English) |

## Introduction

OpenCode Session Manager is a desktop tool for managing [opencode](https://github.com/anomalyco/opencode) session data. It supports both GUI (graphical interface) and TUI (terminal interface) modes, helping you view, delete, compress, and archive your opencode session records.

## Features

| Feature | Description |
|---------|-------------|
| 📋 View | Display all sessions and drafts grouped by workspace, with prompt preview |
| 🗑️ Delete | Batch select and delete unwanted sessions or drafts |
| 🧹 Clean | One-click delete all empty sessions |
| 📦 Compress | VACUUM database to reclaim space from deleted records |
| 💾 Archive | Export sessions to JSON files for backup, with import support |
| 🌐 Language | Support Chinese/English interface switching |

## Requirements

- Python 3.7 or higher
- tkinter (built into Python, needed for GUI mode)

## Installation

```bash
# Clone the repository
git clone https://github.com/VeloxLLM/opencode-session-manager.git

# Enter the project directory
cd opencode-session-manager
```

## Usage

### GUI Mode (Graphical Interface)

```bash
python opencode_session_manager.py
```

### TUI Mode (Terminal Interface)

```bash
python tui.py
```

Or click the "TUI" button in the GUI to launch.

### TUI Shortcuts

| Key | Function |
|-----|----------|
| ↑/↓ | Move up/down |
| Enter | View details |
| d | Delete current session |
| e | Delete empty sessions |
| v | Vacuum database |
| r | Refresh |
| q | Quit |

### Database Location

The program automatically searches for the `drafts.sqlite` file at:

| System | Path |
|--------|------|
| Windows | `%APPDATA%\ai.opencode.desktop\drafts.sqlite` |
| Windows (Local) | `%LOCALAPPDATA%\ai.opencode.desktop\drafts.sqlite` |

If not found, click the "Select Database" button to manually choose the file.

## Interface

### GUI Interface

```
┌─────────────────────────────────────────────────────────────┐
│  [Refresh] [Select DB] │ [Del Empty] [Vacuum] [Archive] [Import] │
├─────────────────────────────────────────────────────────────┤
│ Database Info: path/size/record count                       │
├────────────────────────────┬────────────────────────────────┤
│ Session List               │ Session Details                │
│                            │                                │
│ 📝 Drafts (45)             │ === Key ===                    │
│   ├─ Prompt preview...     │ opencode.draft.xxx:draft:prompt│
│   └─ Prompt preview...     │                                │
│                            │ === Content (JSON) ===         │
│ 📁 Workspaces (20)        │ {                              │
│   ├─ Prompt preview...     │   "prompt": [...]              │
│   └─ Prompt preview...     │ }                              │
│                            │                                │
│ 🌐 Global History          │                                │
└────────────────────────────┴────────────────────────────────┘
```

### TUI Interface

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

## Archive Format

Exported JSON file format:

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

## Database Structure

opencode stores session data in an SQLite database:

| Table | Description |
|-------|-------------|
| `document` | Stores session data (key-value format) |
| `blob` | Stores binary data |

Key name formats:
- `opencode.draft.*:draft:prompt` - Drafts
- `opencode.workspace.*.dat:session:ses_*:prompt` - Workspace sessions
- `opencode.global.dat:prompt-history` - Global history

## Contributing

Issues and Pull Requests are welcome!

## License

GPL 3.0 - See [LICENSE](LICENSE) file for details
