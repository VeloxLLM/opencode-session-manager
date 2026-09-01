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
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class OpenCodeSessionManager:
    """OpenCode 会话管理器"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OpenCode Session Manager")
        self.root.geometry("1000x700")
        self.root.minsize(800, 500)

        # 数据库路径
        self.db_path = self._find_database()
        self.conn = None
        self.sessions_data = {}

        self._setup_ui()
        self._load_data()

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

        # 让用户手动选择
        return None

    def _setup_ui(self):
        """设置 UI 界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 顶部工具栏
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(toolbar, text="刷新", command=self._load_data).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="选择数据库", command=self._select_database).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(toolbar, text="压缩数据库", command=self._vacuum_database).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="存档选中", command=self._archive_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="导入存档", command=self._import_archive).pack(side=tk.LEFT)

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(toolbar, textvariable=self.status_var).pack(side=tk.RIGHT)

        # 数据库信息
        info_frame = ttk.LabelFrame(main_frame, text="数据库信息", padding="5")
        info_frame.pack(fill=tk.X, pady=(0, 10))

        self.db_info_var = tk.StringVar(value="未加载")
        ttk.Label(info_frame, textvariable=self.db_info_var).pack(anchor=tk.W)

        # 主内容区域 - 使用 PanedWindow
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # 左侧 - 会话列表
        left_frame = ttk.LabelFrame(paned, text="会话列表", padding="5")
        paned.add(left_frame, weight=2)

        # 会话列表树
        tree_frame = ttk.Frame(left_frame)
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
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(btn_frame, text="全选", command=self._select_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="取消全选", command=self._deselect_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="删除选中", command=self._delete_selected).pack(side=tk.RIGHT)

        # 右侧 - 详情预览
        right_frame = ttk.LabelFrame(paned, text="会话详情", padding="5")
        paned.add(right_frame, weight=1)

        self.detail_text = tk.Text(right_frame, wrap=tk.WORD, state=tk.DISABLED)
        detail_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.detail_text.yview)
        self.detail_text.configure(yscrollcommand=detail_scrollbar.set)

        self.detail_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _select_database(self):
        """手动选择数据库文件"""
        path = filedialog.askopenfilename(
            title="选择 opencode drafts.sqlite 文件",
            filetypes=[("SQLite 数据库", "*.sqlite"), ("所有文件", "*.*")]
        )
        if path:
            self.db_path = Path(path)
            self._load_data()

    def _load_data(self):
        """加载会话数据"""
        if not self.db_path or not self.db_path.exists():
            self.status_var.set("错误: 未找到数据库文件")
            self.db_info_var.set("请点击'选择数据库'按钮选择 drafts.sqlite 文件")
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
                f"路径: {self.db_path}\n"
                f"大小: {db_size_str}\n"
                f"总记录: {total_count} | 草稿: {draft_count} | 会话: {session_count}"
            )

            # 加载会话树
            self._load_tree()

            self.status_var.set(f"已加载 {total_count} 条记录")

        except Exception as e:
            messagebox.showerror("错误", f"加载数据库失败:\n{str(e)}")
            self.status_var.set("加载失败")

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
            draft_node = self.tree.insert("", tk.END, text=f"📝 草稿 ({len(drafts)})", open=True)
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
            global_node = self.tree.insert("", tk.END, text="🌐 全局历史", open=False)
            for key, value in global_data:
                self.tree.insert(global_node, tk.END, text="提示词历史", values=(key, value))

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
            return "(空)"
        except:
            return "(无法解析)"

    def _decode_workspace_name(self, encoded_name: str) -> str:
        """解码工作区名称"""
        # 工作区名称格式: opencode.workspace.<encoded_path>.<hash>.dat
        # 编码方式: 路径中的 : 和 \ 被替换
        try:
            # 移除前缀和后缀
            prefix = "opencode.workspace."
            suffix = ".dat"
            if encoded_name.startswith(prefix):
                encoded_name = encoded_name[len(prefix):]
            if encoded_name.endswith(suffix):
                encoded_name = encoded_name[:-len(suffix)]

            # 移除最后的 hash 部分 (格式: .xxxxxxx)
            parts = encoded_name.rsplit(".", 1)
            if len(parts) == 2 and len(parts[1]) >= 6:
                encoded_name = parts[0]

            # 解码路径
            # 替换常见的编码
            decoded = encoded_name.replace("--", ":")
            decoded = decoded.replace("-", "\\")

            # 如果看起来像路径，返回它
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
        self.detail_text.insert(tk.END, "=== 键 ===\n", "header")
        self.detail_text.insert(tk.END, f"{key}\n\n")

        # 尝试格式化 JSON
        try:
            data = json.loads(value)
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
            self.detail_text.insert(tk.END, "=== 内容 (JSON) ===\n", "header")
            self.detail_text.insert(tk.END, formatted)
        except:
            self.detail_text.insert(tk.END, "=== 内容 ===\n", "header")
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
            messagebox.showwarning("警告", "请先选择要删除的会话")
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
        if not messagebox.askyesno("确认删除", f"确定要删除 {count} 条记录吗？\n\n此操作不可撤销！"):
            return

        try:
            cursor = self.conn.cursor()
            placeholders = ",".join(["?"] * len(keys_to_delete))
            cursor.execute(f"DELETE FROM document WHERE key IN ({placeholders})", keys_to_delete)
            self.conn.commit()

            self.status_var.set(f"已删除 {count} 条记录")
            self._load_data()

        except Exception as e:
            messagebox.showerror("错误", f"删除失败:\n{str(e)}")

    def _archive_selected(self):
        """存档选中的会话"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要存档的会话")
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
        default_name = f"opencode_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_path = filedialog.asksaveasfilename(
            title="保存存档",
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json")],
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

            self.status_var.set(f"已存档 {len(archive_data)} 条记录到 {save_path}")
            messagebox.showinfo("成功", f"已保存 {len(archive_data)} 条记录")

        except Exception as e:
            messagebox.showerror("错误", f"存档失败:\n{str(e)}")

    def _import_archive(self):
        """导入存档"""
        # 选择存档文件
        file_path = filedialog.askopenfilename(
            title="选择存档文件",
            filetypes=[("JSON 文件", "*.json")]
        )

        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                archive = json.load(f)

            if "records" not in archive:
                messagebox.showerror("错误", "无效的存档文件格式")
                return

            records = archive["records"]
            count = len(records)

            # 确认导入
            if not messagebox.askyesno("确认导入", f"确定要导入 {count} 条记录吗？\n\n重复的键将被覆盖！"):
                return

            # 导入记录
            cursor = self.conn.cursor()
            for record in records:
                cursor.execute(
                    "INSERT OR REPLACE INTO document (key, value) VALUES (?, ?)",
                    (record["key"], record["value"])
                )
            self.conn.commit()

            self.status_var.set(f"已导入 {count} 条记录")
            self._load_data()

        except Exception as e:
            messagebox.showerror("错误", f"导入失败:\n{str(e)}")

    def _vacuum_database(self):
        """压缩数据库"""
        if not self.conn:
            messagebox.showwarning("警告", "请先加载数据库")
            return

        if not messagebox.askyesno("确认压缩", "确定要压缩数据库吗？\n\n这将清理删除操作留下的空闲空间。"):
            return

        try:
            self.status_var.set("正在压缩数据库...")
            self.root.update()

            # 获取压缩前大小
            size_before = self.db_path.stat().st_size

            # 执行 VACUUM
            self.conn.execute("VACUUM")

            # 获取压缩后大小
            size_after = self.db_path.stat().st_size

            saved = size_before - size_after
            self.status_var.set(f"压缩完成，节省了 {self._format_size(saved)}")
            messagebox.showinfo(
                "完成",
                f"数据库压缩完成！\n\n"
                f"压缩前: {self._format_size(size_before)}\n"
                f"压缩后: {self._format_size(size_after)}\n"
                f"节省: {self._format_size(saved)}"
            )

            self._load_data()

        except Exception as e:
            messagebox.showerror("错误", f"压缩失败:\n{str(e)}")

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
