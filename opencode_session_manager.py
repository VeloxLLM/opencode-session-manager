#!/usr/bin/env python3
"""
OpenCode Session Manager
管理 opencode 会话的 GUI 工具
功能：查看、删除、压缩、存档
"""

import os
import sys
import json
import shutil
import sqlite3
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional


# 翻译字典
TRANSLATIONS = {
    "zh": {
        "window_title": "OpenCode 会话管理器",
        "refresh": "刷新",
        "select_db": "选择数据库",
        "delete_empty": "删除空会话",
        "vacuum": "压缩数据库",
        "archive": "存档选中",
        "import_archive": "导入存档",
        "launch_tui": "终端版",
        "lang_switch": "English",
        "status_ready": "就绪",
        "db_info_title": "数据库信息",
        "db_info_empty": "未加载",
        "session_list_title": "会话列表",
        "session_detail_title": "会话详情",
        "select_all": "全选",
        "deselect_all": "取消全选",
        "delete_selected": "删除选中",
        "drafts": "草稿",
        "workspaces": "工作区",
        "global_history": "全局历史",
        "prompt_history": "提示词历史",
        "key_header": "=== 键 ===",
        "content_header_json": "=== 内容 (JSON) ===",
        "content_header": "=== 内容 ===",
        "empty": "(空)",
        "parse_error": "(无法解析)",
        "db_not_found_title": "未找到数据库",
        "db_not_found_msg": "请点击「选择数据库」按钮选择 drafts.sqlite 文件",
        "db_load_error": "加载数据库失败",
        "select_db_title": "选择 opencode drafts.sqlite 文件",
        "db_types": [("SQLite 数据库", "*.sqlite"), ("所有文件", "*.*")],
        "records_loaded": "已加载 {} 条记录",
        "load_failed": "加载失败",
        "no_selection_warning": "请先选择要删除的会话",
        "confirm_delete_title": "确认删除",
        "confirm_delete_msg": "确定要删除 {} 条记录吗？\n\n此操作不可撤销！",
        "deleted_records": "已删除 {} 条记录",
        "delete_error": "删除失败",
        "no_empty_sessions": "没有找到空会话",
        "confirm_delete_empty_title": "确认删除",
        "confirm_delete_empty_msg": "找到 {} 个空会话，确定要删除吗？\n\n此操作不可撤销！",
        "deleted_empty_sessions": "已删除 {} 个空会话",
        "delete_empty_error": "删除空会话失败",
        "no_db_warning": "请先加载数据库",
        "confirm_vacuum_title": "确认压缩",
        "confirm_vacuum_msg": "确定要压缩数据库吗？\n\n这将清理删除操作留下的空闲空间。",
        "vacuuming": "正在压缩数据库...",
        "vacuum_complete": "压缩完成",
        "vacuum_before": "压缩前: {}",
        "vacuum_after": "压缩后: {}",
        "vacuum_saved": "节省: {}",
        "vacuum_error": "压缩失败",
        "no_selection_archive_warning": "请先选择要存档的会话",
        "save_archive_title": "保存存档",
        "archive_types": [("JSON 文件", "*.json")],
        "archive_default_name": "opencode_archive_{}.json",
        "archive_saved": "已存档 {} 条记录到 {}",
        "archive_success": "已保存 {} 条记录",
        "archive_error": "存档失败",
        "select_archive_title": "选择存档文件",
        "invalid_archive": "无效的存档文件格式",
        "confirm_import_title": "确认导入",
        "confirm_import_msg": "确定要导入 {} 条记录吗？\n\n重复的键将被覆盖！",
        "imported_records": "已导入 {} 条记录",
        "import_error": "导入失败",
    },
    "en": {
        "window_title": "OpenCode Session Manager",
        "refresh": "Refresh",
        "select_db": "Select DB",
        "delete_empty": "Delete Empty",
        "vacuum": "Vacuum DB",
        "archive": "Archive",
        "import_archive": "Import",
        "launch_tui": "TUI",
        "lang_switch": "中文",
        "status_ready": "Ready",
        "db_info_title": "Database Info",
        "db_info_empty": "Not loaded",
        "session_list_title": "Session List",
        "session_detail_title": "Session Detail",
        "select_all": "Select All",
        "deselect_all": "Deselect All",
        "delete_selected": "Delete Selected",
        "drafts": "Drafts",
        "workspaces": "Workspaces",
        "global_history": "Global History",
        "prompt_history": "Prompt History",
        "key_header": "=== Key ===",
        "content_header_json": "=== Content (JSON) ===",
        "content_header": "=== Content ===",
        "empty": "(empty)",
        "parse_error": "(parse error)",
        "db_not_found_title": "Database Not Found",
        "db_not_found_msg": "Please click 'Select DB' to choose drafts.sqlite file",
        "db_load_error": "Failed to load database",
        "select_db_title": "Select opencode drafts.sqlite file",
        "db_types": [("SQLite Database", "*.sqlite"), ("All Files", "*.*")],
        "records_loaded": "Loaded {} records",
        "load_failed": "Load failed",
        "no_selection_warning": "Please select sessions to delete first",
        "confirm_delete_title": "Confirm Delete",
        "confirm_delete_msg": "Delete {} records?\n\nThis action cannot be undone!",
        "deleted_records": "Deleted {} records",
        "delete_error": "Delete failed",
        "no_empty_sessions": "No empty sessions found",
        "confirm_delete_empty_title": "Confirm Delete",
        "confirm_delete_empty_msg": "Found {} empty sessions, delete them?\n\nThis action cannot be undone!",
        "deleted_empty_sessions": "Deleted {} empty sessions",
        "delete_empty_error": "Failed to delete empty sessions",
        "no_db_warning": "Please load database first",
        "confirm_vacuum_title": "Confirm Vacuum",
        "confirm_vacuum_msg": "Vacuum database?\n\nThis will reclaim space from deleted records.",
        "vacuuming": "Vacuuming database...",
        "vacuum_complete": "Vacuum Complete",
        "vacuum_before": "Before: {}",
        "vacuum_after": "After: {}",
        "vacuum_saved": "Saved: {}",
        "vacuum_error": "Vacuum failed",
        "no_selection_archive_warning": "Please select sessions to archive first",
        "save_archive_title": "Save Archive",
        "archive_types": [("JSON Files", "*.json")],
        "archive_default_name": "opencode_archive_{}.json",
        "archive_saved": "Archived {} records to {}",
        "archive_success": "Saved {} records",
        "archive_error": "Archive failed",
        "select_archive_title": "Select Archive File",
        "invalid_archive": "Invalid archive file format",
        "confirm_import_title": "Confirm Import",
        "confirm_import_msg": "Import {} records?\n\nDuplicate keys will be overwritten!",
        "imported_records": "Imported {} records",
        "import_error": "Import failed",
    }
}


class OpenCodeSessionManager:
    """OpenCode 会话管理器"""

    def __init__(self):
        self.root = tk.Tk()
        self.lang = "zh"  # 默认中文
        self._ = TRANSLATIONS[self.lang]

        self.root.title(self._["window_title"])
        self.root.geometry("1000x700")
        self.root.minsize(800, 500)

        # 数据库路径
        self.db_path = self._find_database()
        self.conn = None
        self.sessions_data = {}

        # UI 组件引用
        self.widgets = {}

        self._setup_ui()
        self._load_data()

    def _t(self, key: str, *args) -> str:
        """翻译函数"""
        text = self._.get(key, key)
        if args:
            text = text.format(*args)
        return text

    def _find_database(self) -> Optional[Path]:
        """查找 opencode 数据库文件"""
        possible_paths = [
            Path(os.environ.get("APPDATA", "")) / "ai.opencode.desktop" / "drafts.sqlite",
            Path(os.environ.get("LOCALAPPDATA", "")) / "ai.opencode.desktop" / "drafts.sqlite",
            Path.home() / "AppData" / "Roaming" / "ai.opencode.desktop" / "drafts.sqlite",
        ]

        for path in possible_paths:
            if path.exists():
                return path

        return None

    def _setup_ui(self):
        """设置 UI 界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 顶部工具栏
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        # 左侧按钮
        self.widgets["btn_refresh"] = ttk.Button(toolbar, text=self._t("refresh"), command=self._load_data)
        self.widgets["btn_refresh"].pack(side=tk.LEFT, padx=(0, 5))

        self.widgets["btn_select_db"] = ttk.Button(toolbar, text=self._t("select_db"), command=self._select_database)
        self.widgets["btn_select_db"].pack(side=tk.LEFT, padx=(0, 5))

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        self.widgets["btn_delete_empty"] = ttk.Button(toolbar, text=self._t("delete_empty"), command=self._delete_empty_sessions)
        self.widgets["btn_delete_empty"].pack(side=tk.LEFT, padx=(0, 5))

        self.widgets["btn_vacuum"] = ttk.Button(toolbar, text=self._t("vacuum"), command=self._vacuum_database)
        self.widgets["btn_vacuum"].pack(side=tk.LEFT, padx=(0, 5))

        self.widgets["btn_archive"] = ttk.Button(toolbar, text=self._t("archive"), command=self._archive_selected)
        self.widgets["btn_archive"].pack(side=tk.LEFT, padx=(0, 5))

        self.widgets["btn_import"] = ttk.Button(toolbar, text=self._t("import_archive"), command=self._import_archive)
        self.widgets["btn_import"].pack(side=tk.LEFT)

        # 语言切换按钮
        self.widgets["btn_lang"] = ttk.Button(toolbar, text=self._t("lang_switch"), command=self._switch_language)
        self.widgets["btn_lang"].pack(side=tk.LEFT, padx=(10, 0))

        # 启动 TUI 按钮
        self.widgets["btn_tui"] = ttk.Button(toolbar, text=self._t("launch_tui"), command=self._launch_tui)
        self.widgets["btn_tui"].pack(side=tk.LEFT, padx=(5, 0))

        # 状态栏
        self.status_var = tk.StringVar(value=self._t("status_ready"))
        self.widgets["status"] = ttk.Label(toolbar, textvariable=self.status_var)
        self.widgets["status"].pack(side=tk.RIGHT)

        # 数据库信息
        self.widgets["info_frame"] = ttk.LabelFrame(main_frame, text=self._t("db_info_title"), padding="5")
        self.widgets["info_frame"].pack(fill=tk.X, pady=(0, 10))

        self.db_info_var = tk.StringVar(value=self._t("db_info_empty"))
        self.widgets["db_info"] = ttk.Label(self.widgets["info_frame"], textvariable=self.db_info_var)
        self.widgets["db_info"].pack(anchor=tk.W)

        # 主内容区域 - 使用 PanedWindow
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # 左侧 - 会话列表
        self.widgets["left_frame"] = ttk.LabelFrame(paned, text=self._t("session_list_title"), padding="5")
        paned.add(self.widgets["left_frame"], weight=2)

        # 会话列表树
        tree_frame = ttk.Frame(self.widgets["left_frame"])
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(tree_frame, show="tree", selectmode="extended")
        tree_scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scrollbar_y.set, xscrollcommand=tree_scrollbar_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        tree_scrollbar_y.grid(row=0, column=1, sticky="ns")
        tree_scrollbar_x.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # 列表操作按钮
        btn_frame = ttk.Frame(self.widgets["left_frame"])
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        self.widgets["btn_select_all"] = ttk.Button(btn_frame, text=self._t("select_all"), command=self._select_all)
        self.widgets["btn_select_all"].pack(side=tk.LEFT, padx=(0, 5))

        self.widgets["btn_deselect_all"] = ttk.Button(btn_frame, text=self._t("deselect_all"), command=self._deselect_all)
        self.widgets["btn_deselect_all"].pack(side=tk.LEFT, padx=(0, 5))

        self.widgets["btn_delete_selected"] = ttk.Button(btn_frame, text=self._t("delete_selected"), command=self._delete_selected)
        self.widgets["btn_delete_selected"].pack(side=tk.RIGHT)

        # 右侧 - 详情预览
        self.widgets["right_frame"] = ttk.LabelFrame(paned, text=self._t("session_detail_title"), padding="5")
        paned.add(self.widgets["right_frame"], weight=1)

        self.detail_text = tk.Text(self.widgets["right_frame"], wrap=tk.WORD, state=tk.DISABLED)
        detail_scrollbar = ttk.Scrollbar(self.widgets["right_frame"], orient=tk.VERTICAL, command=self.detail_text.yview)
        self.detail_text.configure(yscrollcommand=detail_scrollbar.set)

        self.detail_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _switch_language(self):
        """切换语言"""
        self.lang = "en" if self.lang == "zh" else "zh"
        self._ = TRANSLATIONS[self.lang]
        self._update_ui_text()

    def _launch_tui(self):
        """启动 TUI 版本"""
        tui_path = Path(__file__).parent / "tui.py"
        if not tui_path.exists():
            messagebox.showerror("Error", "tui.py not found")
            return

        # 启动新终端窗口
        try:
            if sys.platform == "win32":
                # 使用 cmd /start 打开新终端窗口
                subprocess.Popen(
                    f'start cmd /k python "{tui_path}"',
                    shell=True
                )
            else:
                subprocess.Popen(["python3", str(tui_path)])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch TUI:\n{str(e)}")

    def _update_ui_text(self):
        """更新所有 UI 文本"""
        self.root.title(self._t("window_title"))

        # 工具栏按钮
        self.widgets["btn_refresh"].configure(text=self._t("refresh"))
        self.widgets["btn_select_db"].configure(text=self._t("select_db"))
        self.widgets["btn_delete_empty"].configure(text=self._t("delete_empty"))
        self.widgets["btn_vacuum"].configure(text=self._t("vacuum"))
        self.widgets["btn_archive"].configure(text=self._t("archive"))
        self.widgets["btn_import"].configure(text=self._t("import_archive"))
        self.widgets["btn_lang"].configure(text=self._t("lang_switch"))
        self.widgets["btn_tui"].configure(text=self._t("launch_tui"))

        # 标签框
        self.widgets["info_frame"].configure(text=self._t("db_info_title"))
        self.widgets["left_frame"].configure(text=self._t("session_list_title"))
        self.widgets["right_frame"].configure(text=self._t("session_detail_title"))

        # 底部按钮
        self.widgets["btn_select_all"].configure(text=self._t("select_all"))
        self.widgets["btn_deselect_all"].configure(text=self._t("deselect_all"))
        self.widgets["btn_delete_selected"].configure(text=self._t("delete_selected"))

        # 刷新树
        self._load_tree()

    def _select_database(self):
        """手动选择数据库文件"""
        path = filedialog.askopenfilename(
            title=self._t("select_db_title"),
            filetypes=self._t("db_types")
        )
        if path:
            self.db_path = Path(path)
            self._load_data()

    def _load_data(self):
        """加载会话数据"""
        if not self.db_path or not self.db_path.exists():
            self.status_var.set(self._t("db_not_found_title"))
            self.db_info_var.set(self._t("db_not_found_msg"))
            return

        try:
            # 关闭旧连接
            if self.conn:
                self.conn.close()

            # 打开新连接
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row

            # 获取数据库信息
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM document")
            total_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM document WHERE key LIKE '%:draft:%'")
            draft_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM document WHERE key LIKE '%:session:%'")
            session_count = cursor.fetchone()[0]

            # 数据库文件大小
            db_size = self.db_path.stat().st_size
            db_size_str = self._format_size(db_size)

            self.db_info_var.set(
                f"{'路径' if self.lang == 'zh' else 'Path'}: {self.db_path}\n"
                f"{'大小' if self.lang == 'zh' else 'Size'}: {db_size_str}\n"
                f"{'总记录' if self.lang == 'zh' else 'Total'}: {total_count} | "
                f"{self._t('drafts')}: {draft_count} | "
                f"{'会话' if self.lang == 'zh' else 'Sessions'}: {session_count}"
            )

            # 加载会话树
            self._load_tree()

            self.status_var.set(self._t("records_loaded", total_count))

        except Exception as e:
            messagebox.showerror(self._t("db_load_error"), f"{self._t('db_load_error')}:\n{str(e)}")
            self.status_var.set(self._t("load_failed"))

    def _load_tree(self):
        """加载会话树"""
        # 清空树
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.conn:
            return

        cursor = self.conn.cursor()
        cursor.execute("SELECT key, value FROM document ORDER BY key")
        rows = cursor.fetchall()

        # 按类型和工作区分组
        drafts = []
        workspaces = {}
        global_data = []

        for row in rows:
            key = row["key"]
            value = row["value"]

            if ":draft:" in key:
                drafts.append((key, value))
            elif ":session:" in key:
                # 解析工作区
                parts = key.split(":")
                if len(parts) >= 2:
                    ws_name = parts[0]
                    if ws_name not in workspaces:
                        workspaces[ws_name] = []
                    workspaces[ws_name].append((key, value))
            elif "prompt-history" in key:
                global_data.append((key, value))

        # 添加草稿节点
        if drafts:
            draft_node = self.tree.insert("", tk.END, text=f"📝 {self._t('drafts')} ({len(drafts)})", open=True)
            for key, value in drafts:
                preview = self._extract_preview(value)
                self.tree.insert(draft_node, tk.END, text=preview, values=(key, value))

        # 添加工作区会话节点
        for ws_name, sessions in sorted(workspaces.items()):
            display_name = self._decode_workspace_name(ws_name)
            ws_node = self.tree.insert("", tk.END, text=f"📁 {display_name} ({len(sessions)})", open=False)
            for key, value in sessions:
                preview = self._extract_preview(value)
                self.tree.insert(ws_node, tk.END, text=preview, values=(key, value))

        # 添加全局历史节点
        if global_data:
            global_node = self.tree.insert("", tk.END, text=f"🌐 {self._t('global_history')}", open=False)
            for key, value in global_data:
                self.tree.insert(global_node, tk.END, text=self._t("prompt_history"), values=(key, value))

    def _extract_preview(self, value: str) -> str:
        """从值中提取预览文本"""
        try:
            data = json.loads(value)
            if "prompt" in data:
                prompt_parts = data["prompt"]
                if isinstance(prompt_parts, list):
                    for part in prompt_parts:
                        if isinstance(part, dict) and "content" in part:
                            content = part["content"]
                            if content:
                                # 截取前50个字符
                                return content[:50] + ("..." if len(content) > 50 else "")
            return self._t("empty")
        except:
            return self._t("parse_error")

    def _decode_workspace_name(self, encoded_name: str) -> str:
        """解码工作区名称"""
        try:
            prefix = "opencode.workspace."
            suffix = ".dat"
            if encoded_name.startswith(prefix):
                encoded_name = encoded_name[len(prefix):]
            if encoded_name.endswith(suffix):
                encoded_name = encoded_name[:-len(suffix)]

            parts = encoded_name.rsplit(".", 1)
            if len(parts) == 2 and len(parts[1]) >= 6:
                encoded_name = parts[0]

            decoded = encoded_name.replace("--", ":")
            decoded = decoded.replace("-", "\\")

            if "\\" in decoded or ":" in decoded:
                return decoded

            return encoded_name
        except:
            return encoded_name

    def _on_select(self, event):
        """树选择事件"""
        selected = self.tree.selection()
        if not selected:
            return

        item = selected[0]
        values = self.tree.item(item, "values")

        if values and len(values) >= 2:
            key, value = values[0], values[1]
            self._show_detail(key, value)

    def _show_detail(self, key: str, value: str):
        """显示详情"""
        self.detail_text.configure(state=tk.NORMAL)
        self.detail_text.delete(1.0, tk.END)

        # 显示键
        self.detail_text.insert(tk.END, self._t("key_header") + "\n", "header")
        self.detail_text.insert(tk.END, f"{key}\n\n")

        # 尝试格式化 JSON
        try:
            data = json.loads(value)
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
            self.detail_text.insert(tk.END, self._t("content_header_json") + "\n", "header")
            self.detail_text.insert(tk.END, formatted)
        except:
            self.detail_text.insert(tk.END, self._t("content_header") + "\n", "header")
            self.detail_text.insert(tk.END, value)

        self.detail_text.configure(state=tk.DISABLED)

    def _select_all(self):
        """全选"""
        for item in self._get_all_leaves():
            self.tree.item(item, tags=("selected",))
            self.tree.selection_add(item)

    def _deselect_all(self):
        """取消全选"""
        self.tree.selection_remove(*self.tree.selection())

    def _get_all_leaves(self):
        """获取所有叶子节点"""
        leaves = []
        for item in self.tree.get_children():
            children = self.tree.get_children(item)
            if children:
                leaves.extend(self._get_all_leaves_from(item))
            else:
                leaves.append(item)
        return leaves

    def _get_all_leaves_from(self, parent):
        """从指定节点获取所有叶子"""
        leaves = []
        children = self.tree.get_children(parent)
        if not children:
            return [parent]
        for child in children:
            leaves.extend(self._get_all_leaves_from(child))
        return leaves

    def _delete_selected(self):
        """删除选中的会话"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(self._t("confirm_delete_title"), self._t("no_selection_warning"))
            return

        # 收集要删除的键
        keys_to_delete = []
        for item in selected:
            values = self.tree.item(item, "values")
            if values and len(values) >= 1:
                keys_to_delete.append(values[0])

        if not keys_to_delete:
            return

        # 确认删除
        count = len(keys_to_delete)
        if not messagebox.askyesno(self._t("confirm_delete_title"), self._t("confirm_delete_msg", count)):
            return

        try:
            cursor = self.conn.cursor()
            placeholders = ",".join(["?"] * len(keys_to_delete))
            cursor.execute(f"DELETE FROM document WHERE key IN ({placeholders})", keys_to_delete)
            self.conn.commit()

            self.status_var.set(self._t("deleted_records", count))
            self._load_data()

        except Exception as e:
            messagebox.showerror(self._t("delete_error"), f"{self._t('delete_error')}:\n{str(e)}")

    def _delete_empty_sessions(self):
        """一键删除空会话"""
        if not self.conn:
            messagebox.showwarning(self._t("confirm_delete_title"), self._t("no_db_warning"))
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT key, value FROM document")
            rows = cursor.fetchall()

            empty_keys = []
            for row in rows:
                key = row["key"]
                value = row["value"]

                # 只处理草稿和会话
                if ":draft:" not in key and ":session:" not in key:
                    continue

                # 检查是否为空
                if self._is_empty_session(value):
                    empty_keys.append(key)

            if not empty_keys:
                messagebox.showinfo(self._t("confirm_delete_title"), self._t("no_empty_sessions"))
                return

            # 确认删除
            count = len(empty_keys)
            if not messagebox.askyesno(self._t("confirm_delete_title"), self._t("confirm_delete_empty_msg", count)):
                return

            # 删除空会话
            placeholders = ",".join(["?"] * len(empty_keys))
            cursor.execute(f"DELETE FROM document WHERE key IN ({placeholders})", empty_keys)
            self.conn.commit()

            self.status_var.set(self._t("deleted_empty_sessions", count))
            self._load_data()

        except Exception as e:
            messagebox.showerror(self._t("delete_empty_error"), f"{self._t('delete_empty_error')}:\n{str(e)}")

    def _is_empty_session(self, value: str) -> bool:
        """检查会话是否为空"""
        try:
            data = json.loads(value)
            if "prompt" in data:
                prompt_parts = data["prompt"]
                if isinstance(prompt_parts, list):
                    for part in prompt_parts:
                        if isinstance(part, dict) and "content" in part:
                            content = part["content"]
                            if content and content.strip():
                                return False
                    return True
            return True
        except:
            return True

    def _archive_selected(self):
        """存档选中的会话"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(self._t("confirm_delete_title"), self._t("no_selection_archive_warning"))
            return

        # 收集要存档的数据
        archive_data = []
        for item in selected:
            values = self.tree.item(item, "values")
            if values and len(values) >= 2:
                archive_data.append({"key": values[0], "value": values[1]})

        if not archive_data:
            return

        # 选择保存位置
        default_name = self._t("archive_default_name", datetime.now().strftime('%Y%m%d_%H%M%S'))
        save_path = filedialog.asksaveasfilename(
            title=self._t("save_archive_title"),
            defaultextension=".json",
            filetypes=self._t("archive_types"),
            initialfile=default_name
        )

        if not save_path:
            return

        try:
            archive = {
                "version": 1,
                "created_at": datetime.now().isoformat(),
                "source": str(self.db_path),
                "records": archive_data
            }

            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(archive, f, indent=2, ensure_ascii=False)

            self.status_var.set(self._t("archive_saved", len(archive_data), save_path))
            messagebox.showinfo(self._t("archive_success"), self._t("archive_success", len(archive_data)))

        except Exception as e:
            messagebox.showerror(self._t("archive_error"), f"{self._t('archive_error')}:\n{str(e)}")

    def _import_archive(self):
        """导入存档"""
        # 选择存档文件
        file_path = filedialog.askopenfilename(
            title=self._t("select_archive_title"),
            filetypes=self._t("archive_types")
        )

        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                archive = json.load(f)

            if "records" not in archive:
                messagebox.showerror(self._t("import_error"), self._t("invalid_archive"))
                return

            records = archive["records"]
            count = len(records)

            # 确认导入
            if not messagebox.askyesno(self._t("confirm_import_title"), self._t("confirm_import_msg", count)):
                return

            # 导入记录
            cursor = self.conn.cursor()
            for record in records:
                cursor.execute(
                    "INSERT OR REPLACE INTO document (key, value) VALUES (?, ?)",
                    (record["key"], record["value"])
                )
            self.conn.commit()

            self.status_var.set(self._t("imported_records", count))
            self._load_data()

        except Exception as e:
            messagebox.showerror(self._t("import_error"), f"{self._t('import_error')}:\n{str(e)}")

    def _vacuum_database(self):
        """压缩数据库"""
        if not self.conn:
            messagebox.showwarning(self._t("confirm_vacuum_title"), self._t("no_db_warning"))
            return

        if not messagebox.askyesno(self._t("confirm_vacuum_title"), self._t("confirm_vacuum_msg")):
            return

        try:
            self.status_var.set(self._t("vacuuming"))
            self.root.update()

            # 获取压缩前大小
            size_before = self.db_path.stat().st_size

            # 执行 VACUUM
            self.conn.execute("VACUUM")

            # 获取压缩后大小
            size_after = self.db_path.stat().st_size

            saved = size_before - size_after
            self.status_var.set(f"{self._t('vacuum_complete')} - {self._t('vacuum_saved', self._format_size(saved))}")
            messagebox.showinfo(
                self._t("vacuum_complete"),
                f"{self._t('vacuum_complete')}\n\n"
                f"{self._t('vacuum_before', self._format_size(size_before))}\n"
                f"{self._t('vacuum_after', self._format_size(size_after))}\n"
                f"{self._t('vacuum_saved', self._format_size(saved))}"
            )

            self._load_data()

        except Exception as e:
            messagebox.showerror(self._t("vacuum_error"), f"{self._t('vacuum_error')}:\n{str(e)}")

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"

    def run(self):
        """运行应用"""
        self.root.mainloop()

        # 关闭数据库连接
        if self.conn:
            self.conn.close()


def main():
    app = OpenCodeSessionManager()
    app.run()


if __name__ == "__main__":
    main()
