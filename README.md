# OpenCode Session Manager

管理 opencode 会话的 GUI 工具

## 功能

- **查看** - 按工作区分组显示所有会话和草稿，支持预览提示词内容
- **删除** - 批量选择并删除不需要的会话或草稿
- **压缩** - VACUUM 数据库，清理删除操作留下的空闲空间
- **存档** - 导出会话到 JSON 文件进行备份，支持导入恢复

## 系统要求

- Python 3.7+
- tkinter（Python 内置）

## 使用方法

```bash
python opencode_session_manager.py
```

## 数据库位置

程序会自动查找以下位置的 `drafts.sqlite` 文件：

- `%APPDATA%\ai.opencode.desktop\drafts.sqlite`
- `%LOCALAPPDATA%\ai.opencode.desktop\drafts.sqlite`

如果未找到，可以点击"选择数据库"按钮手动选择。

## 界面说明

- **左侧树形列表**：显示所有会话，按类型分组（草稿、工作区、全局历史）
- **右侧详情面板**：显示选中会话的详细内容
- **工具栏**：提供刷新、压缩、存档等操作按钮

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
      "value": "{...}"
    }
  ]
}
```

## 许可证

MIT License
