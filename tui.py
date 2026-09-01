#!/usr/bin/env python3
"""
OpenCode Session Manager - TUI Version (Windows Compatible)
终端界面版本，不依赖 curses
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional


# ANSI 颜色代码
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BG_CYAN = "\033[46m"
    BG_BLACK = "\033[40m"


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def set_cursor_visible(visible):
    if os.name == 'nt':
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleCursorInfo(kernel32.GetStdHandle(-11), ctypes.byref(ctypes.c_ulong(1 if visible else 0)))
    else:
        print("\033[?25h" if visible else "\033[?25l", end="")


class OpenCodeSessionManagerTUI:
    """OpenCode 会话管理器 - TUI 版本 (Windows Compatible)"""

    def __init__(self):
        self.db_path = self._find_database()
        self.conn = None
        self.sessions = []
        self.current_index = 0
        self.message = ""
        self.message_color = Colors.GREEN

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
            self.message = "Database not found!"
            self.message_color = Colors.RED
            return

        try:
            if self.conn:
                self.conn.close()
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row

            cursor = self.conn.cursor()
            cursor.execute("SELECT key, value FROM document ORDER BY key")
            self.sessions = [(row["key"], row["value"]) for row in cursor.fetchall()]
            self.message = f"Loaded {len(self.sessions)} records"
            self.message_color = Colors.GREEN
        except Exception as e:
            self.message = f"Load error: {e}"
            self.message_color = Colors.RED

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
                                return content[:50] + ("..." if len(content) > 50 else "")
            return "(empty)"
        except:
            return "(error)"

    def _draw(self):
        """绘制界面"""
        clear_screen()
        height = 30  # 固定高度
        width = 80

        # 标题
        print(f"{Colors.BG_CYAN}{Colors.BLACK}{' OpenCode Session Manager (TUI) ':^{width}}{Colors.RESET}")
        print(f" {Colors.CYAN}Sessions: {len(self.sessions)}{Colors.RESET}")
        print("─" * width)

        # 消息
        if self.message:
            print(f" {self.message_color}{self.message}{Colors.RESET}")
            self.message = ""
        else:
            print()

        # 会话列表
        max_items = height - 8
        start = max(0, self.current_index - max_items + 1)
        end = min(len(self.sessions), start + max_items)

        for i in range(start, end):
            key, value = self.sessions[i]
            preview = self._extract_preview(value)

            prefix = "   "
            if i == self.current_index:
                prefix = f"{Colors.BG_CYAN}{Colors.BLACK} > {Colors.RESET}"
                print(f"{prefix} {Colors.WHITE}{i+1:>4}. {preview}{Colors.RESET}")
            else:
                print(f"{prefix} {i+1:>4}. {preview}")

        # 填充空行
        for _ in range(max_items - (end - start)):
            print()

        # 帮助
        print("─" * width)
        print(f" {Colors.YELLOW}↑/↓:Move  Enter:Detail  d:Delete  e:DelEmpty  v:Vacuum  r:Refresh  q:Quit{Colors.RESET}")

    def _show_detail(self, key: str, value: str):
        """显示详情"""
        clear_screen()
        print(f"{Colors.BG_CYAN}{Colors.BLACK}{' Session Detail ':^{80}}{Colors.RESET}")
        print(f"\n {Colors.CYAN}Key:{Colors.RESET} {key[:75]}")

        try:
            data = json.loads(value)
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
        except:
            formatted = value

        print(f"\n {Colors.CYAN}Content:{Colors.RESET}")
        for line in formatted.split('\n')[:20]:
            print(f" {line}")

        print(f"\n {Colors.YELLOW}Press any key to return...{Colors.RESET}")
        input()

    def _delete_current(self):
        """删除当前会话"""
        if not self.sessions or not self.conn:
            return

        key, _ = self.sessions[self.current_index]
        print(f"\n {Colors.RED}Delete this session? (y/n){Colors.RESET}", end="")
        ch = input().strip().lower()

        if ch == 'y':
            try:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM document WHERE key = ?", (key,))
                self.conn.commit()
                self._load_data()
                if self.current_index >= len(self.sessions):
                    self.current_index = max(0, len(self.sessions) - 1)
            except Exception as e:
                self.message = f"Delete error: {e}"
                self.message_color = Colors.RED

    def _delete_empty_sessions(self):
        """删除所有空会话"""
        if not self.conn:
            return

        empty_count = 0
        empty_keys = []
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
                            empty_keys.append(key)
            except:
                empty_count += 1
                empty_keys.append(key)

        if empty_count == 0:
            self.message = "No empty sessions found"
            self.message_color = Colors.GREEN
            return

        print(f"\n {Colors.YELLOW}Delete {empty_count} empty sessions? (y/n){Colors.RESET}", end="")
        ch = input().strip().lower()

        if ch == 'y':
            try:
                cursor = self.conn.cursor()
                for key in empty_keys:
                    cursor.execute("DELETE FROM document WHERE key = ?", (key,))
                self.conn.commit()
                self._load_data()
                self.message = f"Deleted {empty_count} empty sessions"
                self.message_color = Colors.GREEN
            except Exception as e:
                self.message = f"Delete error: {e}"
                self.message_color = Colors.RED

    def _vacuum_database(self):
        """压缩数据库"""
        if not self.conn:
            return

        try:
            size_before = self.db_path.stat().st_size
            self.conn.execute("VACUUM")
            size_after = self.db_path.stat().st_size
            saved = size_before - size_after
            self.message = f"Vacuum complete! Saved: {saved} bytes"
            self.message_color = Colors.GREEN
        except Exception as e:
            self.message = f"Vacuum error: {e}"
            self.message_color = Colors.RED

    def run(self):
        """主循环"""
        # 启用 Windows ANSI 支持
        if os.name == 'nt':
            os.system('')

        self._load_data()

        while True:
            self._draw()

            # 获取按键
            try:
                if os.name == 'nt':
                    import msvcrt
                    ch = msvcrt.getch()
                    if ch == b'\xe0':  # 方向键前缀
                        ch = msvcrt.getch()
                        if ch == b'H':  # 上
                            if self.current_index > 0:
                                self.current_index -= 1
                        elif ch == b'P':  # 下
                            if self.current_index < len(self.sessions) - 1:
                                self.current_index += 1
                        continue
                    else:
                        ch = ch.decode('utf-8', errors='ignore').lower()
                else:
                    import tty
                    import termios
                    fd = sys.stdin.fileno()
                    old_settings = termios.tcgetattr(fd)
                    try:
                        tty.setraw(sys.stdin.fileno())
                        ch = sys.stdin.read(1)
                    finally:
                        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                        ch = ch.lower()
            except:
                continue

            # 处理按键
            if ch == 'q':
                break
            elif ch == '\r' or ch == '\n':  # Enter
                if self.sessions:
                    key, value = self.sessions[self.current_index]
                    self._show_detail(key, value)
            elif ch == 'd':
                self._delete_current()
            elif ch == 'e':
                self._delete_empty_sessions()
            elif ch == 'v':
                self._vacuum_database()
            elif ch == 'r':
                self._load_data()
                self.current_index = 0

        # 关闭连接
        if self.conn:
            self.conn.close()

        clear_screen()
        print("Goodbye!")


def main():
    app = OpenCodeSessionManagerTUI()
    app.run()


if __name__ == "__main__":
    main()
