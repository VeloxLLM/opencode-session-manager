#!/usr/bin/env python3
"""OpenCode Session Manager - tkinter GUI for v2/v1 session databases."""

from __future__ import annotations

import json
import sqlite3
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Dict, List, Optional

try:
    import opencode_core as core
except ImportError:  # allow `python py/opencode_session_manager.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import opencode_core as core


TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "zh": {
        "window_title": "OpenCode 会话管理器 v2",
        "language": "中/EN",
        "refresh": "刷新",
        "select_db": "选择数据库",
        "vacuum": "压缩数据库",
        "export": "导出选中",
        "import": "导入存档",
        "delete_archived": "删除已归档",
        "archive_manager": "归档管理",
        "select_all": "全选",
        "deselect_all": "取消全选",
        "delete_selected": "删除选中",
        "search": "搜索",
        "status": "状态",
        "time": "时间",
        "status_all": "全部",
        "status_active": "活跃",
        "status_archived": "已归档",
        "time_all": "全部",
        "time_today": "今天",
        "time_7d": "7天内",
        "time_30d": "30天内",
        "sessions": "会话列表",
        "detail": "会话详情",
        "db_info": "数据库信息",
        "ready": "就绪",
        "no_db": "未找到数据库，请手动选择 opencode.db",
        "no_db_title": "未找到数据库",
        "no_selection": "请先选择会话",
        "confirm_delete": "确认删除",
        "confirm_delete_msg": "确定删除选中的 {} 个会话吗？\n关联消息会一并删除，此操作不可撤销！",
        "confirm_archived_msg": "确定删除全部 {} 个已归档会话吗？\n此操作不可撤销！",
        "deleted": "已删除 {} 个会话",
        "no_archived": "没有已归档的会话",
        "save_archive": "保存存档",
        "archive_saved": "已导出 {} 个会话",
        "archive_failed": "导出失败",
        "select_archive": "选择存档文件",
        "confirm_import": "确认导入",
        "confirm_import_msg": "导入存档会写入当前数据库，重复的会话将被覆盖。继续吗？",
        "import_done": "已导入 {} 个会话、{} 条消息、{} 个片段、{} 条旧记录",
        "import_failed": "导入失败",
        "invalid_archive": "无效的存档文件格式",
        "vacuum_done": "压缩完成，节省 {}",
        "vacuum_failed": "压缩失败",
        "confirm_vacuum": "确认压缩",
        "confirm_vacuum_msg": "压缩会重建数据库文件。请尽量在 opencode 关闭时执行。继续吗？",
        "loaded": "已加载 {} 个会话",
        "load_failed": "加载失败",
        "error": "错误",
        "path": "路径",
        "size": "大小",
        "tables": "数据表",
        "v2": "v2 会话",
        "v1": "v1 会话",
        "archived_count": "已归档",
        "legacy_records": "旧版记录",
        "title": "标题",
        "id": "ID",
        "schema": "数据表",
        "version": "版本",
        "directory": "目录",
        "created": "创建时间",
        "updated": "更新时间",
        "messages": "消息数",
        "tokens": "Token",
        "cost": "费用",
        "archive_db_missing": "未找到桌面版归档数据库 drafts.sqlite",
        "archive_records": "归档记录",
        "archive_hint": "旧版桌面归档数据（document 表）",
    },
    "en": {
        "window_title": "OpenCode Session Manager v2",
        "language": "EN/中",
        "refresh": "Refresh",
        "select_db": "Select DB",
        "vacuum": "Vacuum",
        "export": "Export",
        "import": "Import",
        "delete_archived": "Delete Archived",
        "archive_manager": "Archive Manager",
        "select_all": "Select All",
        "deselect_all": "Deselect All",
        "delete_selected": "Delete Selected",
        "search": "Search",
        "status": "Status",
        "time": "Time",
        "status_all": "All",
        "status_active": "Active",
        "status_archived": "Archived",
        "time_all": "All",
        "time_today": "Today",
        "time_7d": "7 Days",
        "time_30d": "30 Days",
        "sessions": "Sessions",
        "detail": "Details",
        "db_info": "Database",
        "ready": "Ready",
        "no_db": "Database not found. Please select opencode.db manually.",
        "no_db_title": "Database Not Found",
        "no_selection": "Please select sessions first",
        "confirm_delete": "Confirm Delete",
        "confirm_delete_msg": "Delete {} selected session(s)?\nMessages will be removed too. This cannot be undone!",
        "confirm_archived_msg": "Delete all {} archived sessions?\nThis cannot be undone!",
        "deleted": "Deleted {} session(s)",
        "no_archived": "No archived sessions found",
        "save_archive": "Save Archive",
        "archive_saved": "Exported {} session(s)",
        "archive_failed": "Export failed",
        "select_archive": "Select Archive File",
        "confirm_import": "Confirm Import",
        "confirm_import_msg": "Import will write to the current database; duplicate sessions are replaced. Continue?",
        "import_done": "Imported {} sessions, {} messages, {} parts, {} legacy records",
        "import_failed": "Import failed",
        "invalid_archive": "Invalid archive format",
        "vacuum_done": "Vacuum complete, saved {}",
        "vacuum_failed": "Vacuum failed",
        "confirm_vacuum": "Confirm Vacuum",
        "confirm_vacuum_msg": "Vacuum rebuilds the database file. Close opencode first if possible. Continue?",
        "loaded": "Loaded {} session(s)",
        "load_failed": "Load failed",
        "error": "Error",
        "path": "Path",
        "size": "Size",
        "tables": "Tables",
        "v2": "v2 sessions",
        "v1": "v1 sessions",
        "archived_count": "Archived",
        "legacy_records": "Legacy records",
        "title": "Title",
        "id": "ID",
        "schema": "Table",
        "version": "Version",
        "directory": "Directory",
        "created": "Created",
        "updated": "Updated",
        "messages": "Messages",
        "tokens": "Tokens",
        "cost": "Cost",
        "archive_db_missing": "Desktop archive database drafts.sqlite not found",
        "archive_records": "Archive records",
        "archive_hint": "Legacy desktop drafts (document table)",
    },
}

STATUS_KEYS = ("status_all", "status_active", "status_archived")
TIME_KEYS = ("time_all", "time_today", "time_7d", "time_30d")


class ArchiveManagerWindow:
    """Window for the legacy drafts.sqlite document table."""

    def __init__(self, parent: tk.Tk, db_path: Path, lang: str):
        self.db_path = db_path
        self.lang = lang
        self.conn = core.connect(db_path)
        self.window = tk.Toplevel(parent)
        self.window.geometry("820x520")
        self.window.minsize(600, 400)
        self.window.protocol("WM_DELETE_WINDOW", self._close)

        main = ttk.Frame(self.window, padding=10)
        main.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main, text=self.t("archive_hint")).pack(anchor=tk.W, pady=(0, 8))

        frame = ttk.LabelFrame(main, text=self.t("archive_records"), padding=5)
        frame.pack(fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(frame, show="tree", selectmode="extended")
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        buttons = ttk.Frame(main)
        buttons.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(buttons, text=self.t("refresh"), command=self._reload).pack(side=tk.LEFT)
        ttk.Button(buttons, text=self.t("select_all"), command=self._select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons, text=self.t("deselect_all"), command=self._deselect_all).pack(side=tk.LEFT)
        ttk.Button(buttons, text=self.t("delete_selected"), command=self._delete).pack(side=tk.RIGHT)
        self._reload()

    def t(self, key: str, *args) -> str:
        text = TRANSLATIONS[self.lang].get(key, key)
        return text.format(*args) if args else text

    def _reload(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for key, value in core.list_legacy_records(self.conn):
            preview = core.extract_preview(value) or "(empty)"
            self.tree.insert("", tk.END, text=f"{preview[:60]}", values=(key,))

    def _select_all(self) -> None:
        self.tree.selection_add(*self.tree.get_children())

    def _deselect_all(self) -> None:
        self.tree.selection_remove(*self.tree.selection())

    def _delete(self) -> None:
        keys = [self.tree.item(item, "values")[0] for item in self.tree.selection()]
        if not keys:
            messagebox.showwarning(self.t("confirm_delete"), self.t("no_selection"))
            return
        if not messagebox.askyesno(self.t("confirm_delete"), self.t("confirm_delete_msg", len(keys))):
            return
        core.delete_legacy_records(self.conn, keys)
        self._reload()

    def _close(self) -> None:
        self.conn.close()
        self.window.destroy()


class OpenCodeSessionManager:
    def __init__(self):
        self.lang = "zh"
        self.db_path: Optional[Path] = core.find_database()
        self.conn: Optional[sqlite3.Connection] = None
        self.sessions: List[core.SessionInfo] = []
        self.widgets: Dict[str, tk.Widget] = {}

        self.root = tk.Tk()
        self.root.geometry("1100x720")
        self.root.minsize(860, 560)
        self._build_ui()
        self._load_data()

    def t(self, key: str, *args) -> str:
        text = TRANSLATIONS[self.lang].get(key, key)
        return text.format(*args) if args else text

    def _build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        toolbar = ttk.Frame(main)
        toolbar.pack(fill=tk.X, pady=(0, 8))
        specs = [
            ("btn_lang", "language", "_switch_language"),
            ("btn_refresh", "refresh", "_load_data"),
            ("btn_select_db", "select_db", "_select_database"),
            ("btn_vacuum", "vacuum", "_vacuum"),
            ("btn_export", "export", "_export"),
            ("btn_import", "import", "_import"),
            ("btn_archived", "delete_archived", "_delete_archived"),
            ("btn_archive_manager", "archive_manager", "_open_archive_manager"),
        ]
        for name, label, command in specs:
            self.widgets[name] = ttk.Button(toolbar, text=self.t(label), command=getattr(self, command))
            self.widgets[name].pack(side=tk.LEFT, padx=(0, 4))
            if name in {"btn_lang", "btn_select_db", "btn_vacuum", "btn_import"}:
                ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)

        self.status_var = tk.StringVar(value=self.t("ready"))
        ttk.Label(toolbar, textvariable=self.status_var).pack(side=tk.RIGHT)

        info = ttk.LabelFrame(main, text=self.t("db_info"), padding=5)
        info.pack(fill=tk.X, pady=(0, 8))
        self.widgets["info_frame"] = info
        self.db_info_var = tk.StringVar(value=self.t("ready"))
        ttk.Label(info, textvariable=self.db_info_var, justify=tk.LEFT).pack(anchor=tk.W)

        filters = ttk.Frame(main)
        filters.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(filters, text=self.t("search")).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        entry = ttk.Entry(filters, textvariable=self.search_var, width=28)
        entry.pack(side=tk.LEFT, padx=(4, 10))
        entry.bind("<Return>", lambda _: self._load_tree())

        ttk.Label(filters, text=self.t("status")).pack(side=tk.LEFT)
        self.status_filter_var = tk.StringVar(value=self.t(STATUS_KEYS[0]))
        status_values = [self.t(key) for key in STATUS_KEYS]
        self.widgets["status_filter"] = ttk.Combobox(
            filters, textvariable=self.status_filter_var, values=status_values, state="readonly", width=10
        )
        self.widgets["status_filter"].pack(side=tk.LEFT, padx=(4, 10))
        self.widgets["status_filter"].bind("<<ComboboxSelected>>", lambda _: self._load_tree())

        ttk.Label(filters, text=self.t("time")).pack(side=tk.LEFT)
        self.time_filter_var = tk.StringVar(value=self.t(TIME_KEYS[0]))
        time_values = [self.t(key) for key in TIME_KEYS]
        self.widgets["time_filter"] = ttk.Combobox(
            filters, textvariable=self.time_filter_var, values=time_values, state="readonly", width=10
        )
        self.widgets["time_filter"].pack(side=tk.LEFT, padx=4)
        self.widgets["time_filter"].bind("<<ComboboxSelected>>", lambda _: self._load_tree())

        paned = ttk.PanedWindow(main, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        left = ttk.LabelFrame(paned, text=self.t("sessions"), padding=5)
        right = ttk.LabelFrame(paned, text=self.t("detail"), padding=5)
        self.widgets["left_frame"] = left
        self.widgets["right_frame"] = right
        paned.add(left, weight=3)
        paned.add(right, weight=2)

        tree_frame = ttk.Frame(left)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(tree_frame, show="tree", selectmode="extended")
        yscroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        xscroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        buttons = ttk.Frame(left)
        buttons.pack(fill=tk.X, pady=(5, 0))
        self.widgets["btn_select_all"] = ttk.Button(buttons, text=self.t("select_all"), command=self._select_all)
        self.widgets["btn_select_all"].pack(side=tk.LEFT, padx=(0, 4))
        self.widgets["btn_deselect_all"] = ttk.Button(buttons, text=self.t("deselect_all"), command=self._deselect_all)
        self.widgets["btn_deselect_all"].pack(side=tk.LEFT)
        self.widgets["btn_delete"] = ttk.Button(buttons, text=self.t("delete_selected"), command=self._delete_selected)
        self.widgets["btn_delete"].pack(side=tk.RIGHT)

        self.detail_text = tk.Text(right, wrap=tk.WORD, state=tk.DISABLED)
        detail_scroll = ttk.Scrollbar(right, orient=tk.VERTICAL, command=self.detail_text.yview)
        self.detail_text.configure(yscrollcommand=detail_scroll.set)
        self.detail_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        detail_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _switch_language(self) -> None:
        self.lang = "en" if self.lang == "zh" else "zh"
        self._update_texts()
        self._load_tree()

    def _update_texts(self) -> None:
        self.root.title(self.t("window_title"))
        labels = {
            "btn_lang": "language", "btn_refresh": "refresh", "btn_select_db": "select_db",
            "btn_vacuum": "vacuum", "btn_export": "export", "btn_import": "import",
            "btn_archived": "delete_archived", "btn_archive_manager": "archive_manager",
            "btn_select_all": "select_all", "btn_deselect_all": "deselect_all",
            "btn_delete": "delete_selected",
        }
        for name, key in labels.items():
            self.widgets[name].configure(text=self.t(key))
        self.widgets["info_frame"].configure(text=self.t("db_info"))
        self.widgets["left_frame"].configure(text=self.t("sessions"))
        self.widgets["right_frame"].configure(text=self.t("detail"))
        self.widgets["status_filter"].configure(values=[self.t(key) for key in STATUS_KEYS])
        self.widgets["time_filter"].configure(values=[self.t(key) for key in TIME_KEYS])
        self.status_filter_var.set(self.t(STATUS_KEYS[0]))
        self.time_filter_var.set(self.t(TIME_KEYS[0]))
        if self.conn and self.db_path:
            summary = core.get_database_summary(self.conn, self.db_path)
            self.db_info_var.set(self._format_summary(summary))

    def _format_summary(self, summary: dict) -> str:
        counts = summary["counts"]
        return (
            f"{self.t('path')}: {summary['path']}\n"
            f"{self.t('size')}: {core.format_size(summary['size_bytes'])}  |  "
            f"{self.t('v2')}: {counts.get(core.V2_TABLE, 0)}  |  "
            f"{self.t('v1')}: {counts.get(core.V1_TABLE, 0)}  |  "
            f"{self.t('archived_count')}: {summary['archived']}  |  "
            f"{self.t('legacy_records')}: {counts.get(core.LEGACY_TABLE, 0)}"
        )

    def _select_database(self) -> None:
        path = filedialog.askopenfilename(
            title=self.t("select_db"),
            filetypes=[("SQLite", "*.db *.sqlite"), ("All files", "*.*")],
        )
        if path:
            self.db_path = Path(path)
            self._load_data()

    def _load_data(self) -> None:
        if not self.db_path or not self.db_path.is_file():
            self.status_var.set(self.t("no_db"))
            self.db_info_var.set(self.t("no_db"))
            return
        try:
            if self.conn:
                self.conn.close()
            self.conn = core.connect(self.db_path)
            summary = core.get_database_summary(self.conn, self.db_path)
            self.db_info_var.set(self._format_summary(summary))
            self._load_tree()
            self.status_var.set(self.t("loaded", len(self.sessions)))
        except Exception as exc:
            self.status_var.set(self.t("load_failed"))
            messagebox.showerror(self.t("load_failed"), str(exc))

    def _load_tree(self) -> None:
        self.tree.delete(*self.tree.get_children())
        self.sessions = []
        if not self.conn:
            return
        status_label = self.status_filter_var.get()
        time_label = self.time_filter_var.get()
        status_key = STATUS_KEYS[status_label] if status_label in [self.t(k) for k in STATUS_KEYS] else "status_all"
        time_key = TIME_KEYS[time_label] if time_label in [self.t(k) for k in TIME_KEYS] else "time_all"
        status = {"status_all": "all", "status_active": "active", "status_archived": "archived"}[status_key]
        time_range = {"time_all": "all", "time_today": "today", "time_7d": "7d", "time_30d": "30d"}[time_key]

        try:
            self.sessions = core.list_sessions(
                self.conn, status=status, time_range=time_range, search=self.search_var.get()
            )
        except Exception as exc:
            messagebox.showerror(self.t("load_failed"), str(exc))
            return

        groups: Dict[str, List[core.SessionInfo]] = {}
        for session in self.sessions:
            key = session.directory or session.project_id or "(unknown)"
            groups.setdefault(key, []).append(session)

        for directory, items in sorted(groups.items()):
            short = Path(directory.replace("\\", "/")).name or directory
            latest = max(item.time_updated for item in items)
            stamp = datetime.fromtimestamp(latest / 1000).strftime("%m/%d %H:%M")
            group_node = self.tree.insert("", tk.END, text=f"{short} ({len(items)}) [{stamp}]", open=False)
            for item in items:
                updated = datetime.fromtimestamp(item.time_updated / 1000).strftime("%m/%d %H:%M")
                badge = "v2" if item.ref.table == core.V2_TABLE else "v1"
                flag = " [A]" if item.is_archived else ""
                label = f"[{badge}][{updated}] {item.title[:44]}{flag}"
                self.tree.insert(group_node, tk.END, text=label, values=(item.ref.key, json.dumps(item.as_dict(), ensure_ascii=False)))
        self.status_var.set(self.t("loaded", len(self.sessions)))

    def _on_select(self, _event=None) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        if not values or not values[1]:
            return
        data = json.loads(values[1])
        lines = [f"{self.t('title')}: {data['title']}", f"{self.t('id')}: {data['id']}"]
        for key, label in (
            ("table", "schema"), ("version", "version"), ("directory", "directory"),
            ("message_count", "messages"), ("tokens_total", "tokens"), ("cost", "cost"),
        ):
            lines.append(f"{self.t(label)}: {data.get(key, '')}")
        for key, label in (("time_created", "created"), ("time_updated", "updated")):
            value = data.get(key) or 0
            try:
                lines.append(f"{self.t(label)}: {datetime.fromtimestamp(value / 1000).strftime('%Y-%m-%d %H:%M:%S')}")
            except (ValueError, OSError, OverflowError):
                pass
        self.detail_text.configure(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(tk.END, "\n".join(lines))
        self.detail_text.configure(state=tk.DISABLED)

    def _selected_refs(self) -> List[core.SessionRef]:
        refs = []
        for item in self.tree.selection():
            values = self.tree.item(item, "values")
            if not values:
                continue
            try:
                refs.append(core.SessionRef.parse(values[0]))
            except ValueError:
                continue
        return refs

    def _select_all(self) -> None:
        self.tree.selection_add(*[leaf for leaf in self._leaves()])

    def _deselect_all(self) -> None:
        self.tree.selection_remove(*self.tree.selection())

    def _leaves(self):
        for group in self.tree.get_children():
            for leaf in self.tree.get_children(group):
                yield leaf

    def _delete_selected(self) -> None:
        refs = self._selected_refs()
        if not refs:
            messagebox.showwarning(self.t("confirm_delete"), self.t("no_selection"))
            return
        if not messagebox.askyesno(self.t("confirm_delete"), self.t("confirm_delete_msg", len(refs))):
            return
        try:
            count = core.delete_sessions(self.conn, refs)
            self.status_var.set(self.t("deleted", count))
            self._load_data()
        except Exception as exc:
            messagebox.showerror(self.t("error"), str(exc))

    def _delete_archived(self) -> None:
        archived = [session for session in self.sessions if session.is_archived]
        if not archived:
            messagebox.showinfo(self.t("delete_archived"), self.t("no_archived"))
            return
        if not messagebox.askyesno(self.t("confirm_delete"), self.t("confirm_archived_msg", len(archived))):
            return
        try:
            count = core.delete_archived(self.conn)
            self.status_var.set(self.t("deleted", count))
            self._load_data()
        except Exception as exc:
            messagebox.showerror(self.t("error"), str(exc))

    def _export(self) -> None:
        refs = self._selected_refs()
        if not refs:
            messagebox.showwarning(self.t("export"), self.t("no_selection"))
            return
        path = filedialog.asksaveasfilename(
            title=self.t("save_archive"), defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile=f"opencode_sessions_{datetime.now():%Y%m%d_%H%M%S}.json",
        )
        if not path:
            return
        try:
            payload = core.export_sessions(self.conn, refs)
            payload["source"] = str(self.db_path)
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
            self.status_var.set(self.t("archive_saved", len(payload["sessions"])))
        except Exception as exc:
            messagebox.showerror(self.t("archive_failed"), str(exc))

    def _import(self) -> None:
        path = filedialog.askopenfilename(title=self.t("select_archive"), filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if not isinstance(payload, dict):
                raise ValueError(self.t("invalid_archive"))
        except Exception as exc:
            messagebox.showerror(self.t("import_failed"), str(exc))
            return
        if not messagebox.askyesno(self.t("confirm_import"), self.t("confirm_import_msg")):
            return
        try:
            result = core.import_archive(self.conn, payload)
            self.status_var.set(
                self.t("import_done", result["sessions"], result["messages"], result["parts"], result["records"])
            )
            self._load_data()
        except Exception as exc:
            messagebox.showerror(self.t("import_failed"), str(exc))

    def _vacuum(self) -> None:
        if not messagebox.askyesno(self.t("confirm_vacuum"), self.t("confirm_vacuum_msg")):
            return
        try:
            before = core.format_size(self.db_path.stat().st_size)
            core.vacuum_database(self.conn)
            after = core.format_size(self.db_path.stat().st_size)
            self.status_var.set(f"{self.t('vacuum_done')} {before} -> {after}")
            self._load_data()
        except Exception as exc:
            messagebox.showerror(self.t("vacuum_failed"), str(exc))

    def _open_archive_manager(self) -> None:
        path = core.find_archive_database()
        if not path:
            messagebox.showwarning(self.t("archive_manager"), self.t("archive_db_missing"))
            return
        ArchiveManagerWindow(self.root, path, self.lang)

    def run(self) -> None:
        self.root.mainloop()
        if self.conn:
            self.conn.close()


def main() -> None:
    OpenCodeSessionManager().run()


if __name__ == "__main__":
    main()
