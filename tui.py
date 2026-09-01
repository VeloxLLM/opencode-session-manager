#!/usr/bin/env python3
"""
OpenCode Session Manager - TUI Version
终端界面版本，使用 curses 库
"""

import os
import sys
import json
import sqlite3
import curses
from pathlib import Path
from typing import List, Tuple, Optional


class OpenCodeSessionManagerTUI:
    """OpenCode 会话管理器 - TUI 版本"""

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.db_path = self._find_database()
        self.conn = None
        self.sessions = []
        self.current_index = 0
        self.scroll_offset = 0

        # 初始化 curses
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)    # 选中行
        curses.init_pair(2, curses.COLOR_GREEN, -1)                   # 标题
        curses.init_pair(3, curses.COLOR_YELLOW, -1)                  # 警告
        curses.init_pair(4, curses.COLOR_RED, -1)                     # 错误
        curses.init_pair(5, curses.COLOR_CYAN, -1)                    # 信息

        self._load_data()

    def _find_database(self) -> Optional[Path]:
        """查找数据库"""
        possible_paths = [
            Path(os.environ.get("APPDATA", "")) / "ai.opencode.desktop" / "drafts.sqlite",
            Path(os.environ.get("LOCALAPPDATA", "")) / "ai.opencode.desktop" / "drafts.sqlite",
        ]
        for path in possible_paths:
            if path.exists():
                return path
        return None

    def _load_data(self):
        """加载数据"""
        if not self.db_path or not self.db_path.exists():
            return

        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row

            cursor = self.conn.cursor()
            cursor.execute("SELECT key, value FROM document ORDER BY key")
            self.sessions = [(row["key"], row["value"]) for row in cursor.fetchall()]
        except Exception as e:
            self.sessions = []

    def _extract_preview(self, value: str) -> str:
        """提取预览"""
        try:
            data = json.loads(value)
            if "prompt" in data:
                prompt_parts = data["prompt"]
                if isinstance(prompt_parts, list):
                    for part in prompt_parts:
                        if isinstance(part, dict) and "content" in part:
                            content = part["content"]
                            if content:
                                return content[:60] + ("..." if len(content) > 60 else "")
            return "(empty)"
        except:
            return "(error)"

    def _draw_header(self, height, width):
        """绘制标题"""
        title = " OpenCode Session Manager (TUI) "
        self.stdscr.attron(curses.color_pair(2))
        self.stdscr.addstr(0, 0, title.center(width)[:width])
        self.stdscr.attroff(curses.color_pair(2))

        # 状态信息
        status = f" Sessions: {len(self.sessions)} "
        self.stdscr.addstr(0, width - len(status), status)

    def _draw_help(self, height, width):
        """绘制帮助栏"""
        help_text = " q:Quit  d:Delete  e:DeleteEmpty  v:Vacuum  a:Archive  r:Refresh  Enter:Detail "
        y = height - 1
        self.stdscr.attron(curses.color_pair(1))
        self.stdscr.addstr(y, 0, help_text.center(width)[:width])
        self.stdscr.attroff(curses.color_pair(1))

    def _draw_sessions(self, height, width):
        """绘制会话列表"""
        start_y = 1
        max_items = height - 2

        # 计算可见范围
        if self.current_index >= self.scroll_offset + max_items:
            self.scroll_offset = self.current_index - max_items + 1
        if self.current_index < self.scroll_offset:
            self.scroll_offset = self.current_index

        for i in range(max_items):
            idx = self.scroll_offset + i
            if idx >= len(self.sessions):
                break

            key, value = self.sessions[idx]
            preview = self._extract_preview(value)

            # 截断显示
            display = f" {idx + 1:>4}. {preview}"
            display = display[:width - 1]

            if idx == self.current_index:
                self.stdscr.attron(curses.color_pair(1))
                self.stdscr.addstr(start_y + i, 0, display.ljust(width))
                self.stdscr.attroff(curses.color_pair(1))
            else:
                self.stdscr.addstr(start_y + i, 0, display)

    def _draw_detail(self, key: str, value: str, height, width):
        """绘制详情面板（全屏覆盖）"""
        self.stdscr.clear()
        self.stdscr.attron(curses.color_pair(2))
        self.stdscr.addstr(0, 0, " Session Detail (Press any key to close) ".center(width)[:width])
        self.stdscr.attroff(curses.color_pair(2))

        # 键
        self.stdscr.addstr(1, 0, f"Key: {key[:width-5]}")

        # 内容
        try:
            data = json.loads(value)
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
        except:
            formatted = value

        lines = formatted.split('\n')
        for i, line in enumerate(lines):
            if i + 2 >= height - 1:
                break
            self.stdscr.addstr(i + 2, 0, line[:width - 1])

        self.stdscr.refresh()
        self.stdscr.getch()

    def _delete_session(self):
        """删除当前会话"""
        if not self.sessions or not self.conn:
            return

        key = self.sessions[self.current_index][0]

        # 获取窗口尺寸
        height, width = self.stdscr.getmaxyx()

        # 确认
        self.stdscr.clear()
        self.stdscr.attron(curses.color_pair(4))
        self.stdscr.addstr(height // 2, 0, f"Delete this session? (y/n)".center(width))
        self.stdscr.attroff(curses.color_pair(4))

        self.stdscr.refresh()
        ch = self.stdscr.getch()

        if ch == ord('y') or ch == ord('Y'):
            try:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM document WHERE key = ?", (key,))
                self.conn.commit()
                self._load_data()
                if self.current_index >= len(self.sessions):
                    self.current_index = max(0, len(self.sessions) - 1)
            except:
                pass

    def _delete_empty_sessions(self):
        """删除所有空会话"""
        if not self.conn:
            return

        empty_count = 0
        for key, value in self.sessions:
            if ":draft:" not in key and ":session:" not in key:
                continue
            try:
                data = json.loads(value)
                if "prompt" in data:
                    prompt_parts = data["prompt"]
                    if isinstance(prompt_parts, list):
                        is_empty = True
                        for part in prompt_parts:
                            if isinstance(part, dict) and "content" in part:
                                if part["content"] and part["content"].strip():
                                    is_empty = False
                                    break
                        if is_empty:
                            empty_count += 1
            except:
                empty_count += 1

        if empty_count == 0:
            return

        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        self.stdscr.attron(curses.color_pair(3))
        self.stdscr.addstr(height // 2, 0, f"Delete {empty_count} empty sessions? (y/n)".center(width))
        self.stdscr.attroff(curses.color_pair(3))
        self.stdscr.refresh()

        ch = self.stdscr.getch()
        if ch == ord('y') or ch == ord('Y'):
            try:
                cursor = self.conn.cursor()
                deleted = 0
                for key, value in self.sessions:
                    if ":draft:" not in key and ":session:" not in key:
                        continue
                    try:
                        data = json.loads(value)
                        if "prompt" in data:
                            prompt_parts = data["prompt"]
                            if isinstance(prompt_parts, list):
                                is_empty = True
                                for part in prompt_parts:
                                    if isinstance(part, dict) and "content" in part:
                                        if part["content"] and part["content"].strip():
                                            is_empty = False
                                            break
                                if is_empty:
                                    cursor.execute("DELETE FROM document WHERE key = ?", (key,))
                                    deleted += 1
                    except:
                        cursor.execute("DELETE FROM document WHERE key = ?", (key,))
                        deleted += 1
                self.conn.commit()
                self._load_data()
            except:
                pass

    def _vacuum_database(self):
        """压缩数据库"""
        if not self.conn:
            return

        try:
            size_before = self.db_path.stat().st_size
            self.conn.execute("VACUUM")
            size_after = self.db_path.stat().st_size
            saved = size_before - size_after

            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()
            self.stdscr.attron(curses.color_pair(2))
            self.stdscr.addstr(height // 2, 0, f"Vacuum complete! Saved: {saved} bytes".center(width))
            self.stdscr.attroff(curses.color_pair(2))
            self.stdscr.refresh()
            self.stdscr.getch()
        except:
            pass

    def run(self):
        """主循环"""
        while True:
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()

            self._draw_header(height, width)
            self._draw_sessions(height, width)
            self._draw_help(height, width)

            self.stdscr.refresh()

            # 获取按键
            ch = self.stdscr.getch()

            # 退出
            if ch == ord('q') or ch == ord('Q'):
                break

            # 上下移动
            elif ch == curses.KEY_UP:
                if self.current_index > 0:
                    self.current_index -= 1
            elif ch == curses.KEY_DOWN:
                if self.current_index < len(self.sessions) - 1:
                    self.current_index += 1

            # 删除当前
            elif ch == ord('d') or ch == ord('D'):
                self._delete_session()

            # 删除空会话
            elif ch == ord('e') or ch == ord('E'):
                self._delete_empty_sessions()

            # 压缩
            elif ch == ord('v') or ch == ord('V'):
                self._vacuum_database()

            # 刷新
            elif ch == ord('r') or ch == ord('R'):
                self._load_data()
                self.current_index = 0

            # 查看详情
            elif ch == 10:  # Enter
                if self.sessions:
                    key, value = self.sessions[self.current_index]
                    self._draw_detail(key, value, height, width)

        # 关闭连接
        if self.conn:
            self.conn.close()


def main():
    curses.wrapper(OpenCodeSessionManagerTUI)


if __name__ == "__main__":
    main()
