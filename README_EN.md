# OpenCode Session Manager

> A GUI tool for managing opencode sessions

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Introduction

OpenCode Session Manager is a desktop GUI tool for managing [opencode](https://github.com/anomalyco/opencode) session data. It helps you view, delete, compress, and archive your opencode session records.

## Features

| Feature | Description |
|---------|-------------|
| 📋 View | Display all sessions and drafts grouped by workspace, with prompt preview |
| 🗑️ Delete | Batch select and delete unwanted sessions or drafts |
| 📦 Compress | VACUUM database to reclaim space from deleted records |
| 💾 Archive | Export sessions to JSON files for backup, with import support |

## Requirements

- Python 3.7 or higher
- tkinter (built into Python, no additional installation needed)

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/opencode-session-manager.git

# Enter the project directory
cd opencode-session-manager
```

## Usage

```bash
python opencode_session_manager.py
```

### Database Location

The program automatically searches for the `drafts.sqlite` file at:

| System | Path |
|--------|------|
| Windows | `%APPDATA%\ai.opencode.desktop\drafts.sqlite` |
| Windows (Local) | `%LOCALAPPDATA%\ai.opencode.desktop\drafts.sqlite` |

If not found, click the "Select Database" button to manually choose the file.

## Interface

```
┌─────────────────────────────────────────────────────────────┐
│  [Refresh] [Select DB] │ [Vacuum] [Archive] [Import]       │
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

## Development

```bash
# Run the program
python opencode_session_manager.py
```

## Contributing

Issues and Pull Requests are welcome!

## License

MIT License - See [LICENSE](LICENSE) file for details
