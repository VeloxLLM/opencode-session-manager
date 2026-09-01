# OpenCode Session Manager Handoff

> This document is an AI handoff document. Please read this file before continuing work on this repository.

## 1. Pending Tasks & Precautions

### Pending / TODO

- [ ] Add multilingual support (Chinese/English toggle)
- [ ] Add session content editing feature
- [ ] Add session search feature
- [ ] Add batch export feature
- [ ] Add database backup feature
- [ ] Support macOS and Linux path auto-detection
- [ ] Add dark theme support
- [ ] Add session statistics (by time, workspace, etc.)

### Precautions Before Starting

1. This project uses Python + tkinter, no additional dependencies required
2. Database path on Windows is `%APPDATA%\ai.opencode.desktop\drafts.sqlite`
3. Please understand the SQLite database structure before modifying code
4. Do not modify files in the `.git` directory
5. Ensure code runs properly before committing

## 2. History (What We Did & How)

### 2026-09-01

- Initialized project, created basic GUI framework
- Created `opencode_session_manager.py` main program
  - Implemented database connection and reading
  - Implemented session list tree view
  - Implemented detail panel
  - Implemented delete functionality
  - Implemented compress functionality (VACUUM)
  - Implemented archive functionality (export/import JSON)
- Created `README.md` Chinese documentation
- Created `README_EN.md` English documentation
- Created `ai.md` AI handoff document (Chinese)
- Created `ai_EN.md` AI handoff document (English)
- Initialized Git repository, committed initial code

Current repository state:

```text
opencode-session-manager/
├── opencode_session_manager.py  # Main program
├── README.md                    # Chinese documentation
├── README_EN.md                 # English documentation
├── ai.md                        # AI handoff document (Chinese)
├── ai_EN.md                     # AI handoff document (English)
└── .git/                        # Git repository
```

## 3. Why We Did This

### Goal

Provide a simple and easy-to-use GUI tool to help users manage opencode session data. opencode itself doesn't provide session management functionality, making it difficult for users to view, delete, or backup session records.

### Value

- **Data Management**: Help users clean up unnecessary sessions and free up database space
- **Data Backup**: Support exporting sessions to JSON files to prevent data loss
- **Data Recovery**: Support importing sessions from JSON files for easy data migration
- **Usability**: Graphical interface operations, no need to manually operate SQLite database

### Reuse

- Other developers can build more complex session management tools based on this project
- Can serve as a learning example for Python + tkinter GUI development
- Can be extended to support other opencode data management features
