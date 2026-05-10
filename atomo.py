#!/usr/bin/env python3
"""
Atomo - A nano clone text editor in Python
Usage: python atomo.py [filename]
"""

import curses
import sys
import os
from typing import List, Optional, Tuple

# Key code constants
CTRL_X = 24
CTRL_O = 15
CTRL_W = 23
CTRL_K = 11
CTRL_U = 21
CTRL_G = 7
CTRL_A = 1
CTRL_E = 5
CTRL_Z = 26

MAX_UNDO = 200


class AtomoEditor:
    """Main editor class that handles the text editing interface"""

    def __init__(self, stdscr, filename: Optional[str] = None):
        self.stdscr = stdscr
        self.filename = filename
        self.lines: List[str] = []
        self.cursor_y = 0
        self.cursor_x = 0
        self.offset_y = 0
        self.offset_x = 0
        self.modified = False
        self.message = ""
        self.message_type = "info"
        self.cut_buffer = ""
        self.undo_stack: List[Tuple[List[str], int, int]] = []

        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Status bar
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE)   # Title bar
        curses.init_pair(3, curses.COLOR_RED, -1)                    # Error
        curses.init_pair(4, curses.COLOR_GREEN, -1)                  # Success

        curses.curs_set(1)
        self.stdscr.keypad(True)

        if filename:
            self.load_file(filename)
        else:
            self.lines = [""]

    # ------------------------------------------------------------------
    # Undo
    # ------------------------------------------------------------------

    def push_undo(self):
        """Save current state to undo stack before a destructive operation"""
        self.undo_stack.append((list(self.lines), self.cursor_y, self.cursor_x))
        if len(self.undo_stack) > MAX_UNDO:
            self.undo_stack.pop(0)

    def undo(self):
        """Restore the previous state from the undo stack"""
        if not self.undo_stack:
            self.message = "Nothing to undo"
            self.message_type = "info"
            return
        self.lines, self.cursor_y, self.cursor_x = self.undo_stack.pop()
        self.modified = True
        self.message = "Undo"
        self.message_type = "info"
        self.adjust_scroll()

    # ------------------------------------------------------------------
    # File I/O
    # ------------------------------------------------------------------

    def load_file(self, filename: str) -> bool:
        """Load a file into the editor"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    self.lines = f.read().splitlines()
                    if not self.lines:
                        self.lines = [""]
                self.message = f'Read {len(self.lines)} lines from {filename}'
                self.message_type = "success"
            else:
                self.lines = [""]
                self.message = f'New File: {filename}'
                self.message_type = "info"
            self.filename = filename
            self.modified = False
            return True
        except Exception as e:
            self.message = f'Error reading {filename}: {str(e)}'
            self.message_type = "error"
            self.lines = [""]
            return False

    def save_file(self, filename: Optional[str] = None) -> bool:
        """Save the current buffer to a file"""
        if filename:
            self.filename = filename

        if not self.filename:
            return False

        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.lines) + '\n')

            self.modified = False
            self.message = f'Wrote {len(self.lines)} lines to {self.filename}'
            self.message_type = "success"
            return True
        except Exception as e:
            self.message = f'Error writing {self.filename}: {str(e)}'
            self.message_type = "error"
            return False

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def get_dimensions(self) -> Tuple[int, int]:
        """Get usable dimensions (excluding status bars)"""
        max_y, max_x = self.stdscr.getmaxyx()
        return max_y - 4, max_x

    def safe_addstr(self, y, x, text, attr=0):
        """Safely add string to screen, silently truncating at the right edge"""
        max_y, max_x = self.stdscr.getmaxyx()
        if y >= max_y or x >= max_x:
            return

        max_len = max_x - x - 1
        if max_len <= 0:
            return

        text = str(text)[:max_len]

        try:
            if attr:
                self.stdscr.addstr(y, x, text, attr)
            else:
                self.stdscr.addstr(y, x, text)
        except curses.error:
            pass

    def draw_title_bar(self):
        """Draw the top title bar"""
        max_y, max_x = self.stdscr.getmaxyx()
        title = "  GNU nano clone - Atomo"
        filename_display = self.filename if self.filename else "[New Buffer]"
        mod_indicator = " *" if self.modified else ""

        self.stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
        self.safe_addstr(0, 0, " " * (max_x - 1))
        self.safe_addstr(0, 0, title)

        filename_str = f" File: {filename_display}{mod_indicator} "
        if len(filename_str) < max_x - len(title):
            x_pos = (max_x - len(filename_str)) // 2
            self.safe_addstr(0, x_pos, filename_str)

        self.stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

    def draw_status_bar(self):
        """Draw the bottom status bar"""
        max_y, max_x = self.stdscr.getmaxyx()
        status_left = f" Line {self.cursor_y + 1}/{len(self.lines)}  Col {self.cursor_x + 1} "

        self.stdscr.attron(curses.color_pair(1))
        self.safe_addstr(max_y - 2, 0, " " * (max_x - 1))
        self.safe_addstr(max_y - 2, 0, status_left)
        self.stdscr.attroff(curses.color_pair(1))

    def draw_help_bar(self):
        """Draw the bottom help bar with shortcuts"""
        max_y, max_x = self.stdscr.getmaxyx()

        shortcuts = [
            ("^X", "Exit"), ("^O", "Save"), ("^W", "Search"),
            ("^K", "Cut"), ("^U", "Paste"), ("^Z", "Undo"), ("^G", "Help"),
        ]

        help_text = "  "
        for key, desc in shortcuts:
            help_text += f"{key} {desc}   "

        self.stdscr.attron(curses.color_pair(1))
        self.safe_addstr(max_y - 1, 0, " " * (max_x - 1))
        self.safe_addstr(max_y - 1, 0, help_text)
        self.stdscr.attroff(curses.color_pair(1))

    def draw_message(self):
        """Draw message line if there is one"""
        if self.message:
            max_y, max_x = self.stdscr.getmaxyx()
            color = curses.color_pair(3) if self.message_type == "error" else \
                    curses.color_pair(4) if self.message_type == "success" else 0

            self.safe_addstr(max_y - 3, 0, " " * (max_x - 1))
            self.stdscr.attron(color | curses.A_BOLD)
            self.safe_addstr(max_y - 3, 0, f" {self.message}")
            self.stdscr.attroff(color | curses.A_BOLD)

    def draw_buffer(self):
        """Draw the text buffer"""
        height, width = self.get_dimensions()

        for screen_y in range(height):
            buffer_y = screen_y + self.offset_y
            self.safe_addstr(screen_y + 1, 0, " " * width)

            if buffer_y < len(self.lines):
                line = self.lines[buffer_y]
                visible_line = line[self.offset_x:self.offset_x + width]
                self.safe_addstr(screen_y + 1, 0, visible_line)

    def draw(self):
        """Draw the entire interface"""
        self.stdscr.clear()
        self.draw_title_bar()
        self.draw_buffer()
        self.draw_message()
        self.draw_status_bar()
        self.draw_help_bar()

        screen_y = self.cursor_y - self.offset_y + 1
        screen_x = self.cursor_x - self.offset_x
        height, width = self.get_dimensions()

        if 0 <= screen_y < height + 1 and 0 <= screen_x < width:
            self.stdscr.move(screen_y, screen_x)

        self.stdscr.refresh()

    # ------------------------------------------------------------------
    # Scrolling and cursor movement
    # ------------------------------------------------------------------

    def adjust_scroll(self):
        """Adjust scroll offsets to keep cursor visible"""
        height, width = self.get_dimensions()

        if self.cursor_y < self.offset_y:
            self.offset_y = self.cursor_y
        elif self.cursor_y >= self.offset_y + height:
            self.offset_y = self.cursor_y - height + 1

        if self.cursor_x < self.offset_x:
            self.offset_x = self.cursor_x
        elif self.cursor_x >= self.offset_x + width:
            self.offset_x = self.cursor_x - width + 1

    def move_cursor(self, dy: int, dx: int):
        """Move cursor with bounds checking"""
        self.message = ""

        self.cursor_y = max(0, min(len(self.lines) - 1, self.cursor_y + dy))

        current_line = self.lines[self.cursor_y]
        self.cursor_x = max(0, min(len(current_line), self.cursor_x + dx))

        self.adjust_scroll()

    # ------------------------------------------------------------------
    # Editing operations
    # ------------------------------------------------------------------

    def insert_char(self, char: str):
        """Insert text at cursor position"""
        self.push_undo()
        line = self.lines[self.cursor_y]
        self.lines[self.cursor_y] = line[:self.cursor_x] + char + line[self.cursor_x:]
        self.cursor_x += len(char)  # FIX: was += 1, which broke Tab (4 spaces → cursor off by 3)
        self.modified = True
        self.message = ""
        self.adjust_scroll()

    def delete_char(self):
        """Delete character at cursor (Delete key)"""
        self.push_undo()
        line = self.lines[self.cursor_y]

        if self.cursor_x < len(line):
            self.lines[self.cursor_y] = line[:self.cursor_x] + line[self.cursor_x + 1:]
            self.modified = True
        elif self.cursor_y < len(self.lines) - 1:
            self.lines[self.cursor_y] = line + self.lines[self.cursor_y + 1]
            self.lines.pop(self.cursor_y + 1)
            self.modified = True

        self.message = ""

    def backspace(self):
        """Delete character before cursor (Backspace key)"""
        self.push_undo()
        if self.cursor_x > 0:
            line = self.lines[self.cursor_y]
            self.lines[self.cursor_y] = line[:self.cursor_x - 1] + line[self.cursor_x:]
            self.cursor_x -= 1
            self.modified = True
        elif self.cursor_y > 0:
            prev_line_len = len(self.lines[self.cursor_y - 1])
            self.lines[self.cursor_y - 1] += self.lines[self.cursor_y]
            self.lines.pop(self.cursor_y)
            self.cursor_y -= 1
            self.cursor_x = prev_line_len
            self.modified = True

        self.message = ""
        self.adjust_scroll()

    def insert_newline(self):
        """Insert a new line at cursor position"""
        self.push_undo()
        line = self.lines[self.cursor_y]
        self.lines[self.cursor_y] = line[:self.cursor_x]
        self.lines.insert(self.cursor_y + 1, line[self.cursor_x:])
        self.cursor_y += 1
        self.cursor_x = 0
        self.modified = True
        self.message = ""
        self.adjust_scroll()

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------

    def prompt_input(self, prompt_text: str, default: str = "") -> str:
        """Render an inline prompt at the message line and return user input"""
        max_y, max_x = self.stdscr.getmaxyx()

        self.stdscr.attron(curses.color_pair(1))
        self.safe_addstr(max_y - 3, 0, " " * (max_x - 1))
        self.safe_addstr(max_y - 3, 0, prompt_text)
        self.stdscr.attroff(curses.color_pair(1))

        self.stdscr.refresh()
        curses.echo()
        try:
            col = min(len(prompt_text), max_x - 2)
            self.stdscr.move(max_y - 3, col)
            raw = self.stdscr.getstr(max_y - 3, col, max(1, max_x - len(prompt_text) - 1))
            input_str = raw.decode('utf-8')
        except Exception:
            input_str = ""
        curses.noecho()

        input_str = ''.join(c for c in input_str if c.isprintable()).strip()
        return input_str if input_str else default

    def prompt_save_filename(self) -> str:
        """Prompt user for filename to save"""
        prompt = f"File Name to Write: {self.filename if self.filename else ''}"
        return self.prompt_input(prompt, default=self.filename or "")

    def prompt_search(self) -> Optional[str]:
        """Prompt user for search text"""
        result = self.prompt_input("Search: ")
        return result if result else None

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str):
        """Search for text in buffer, wrapping around at EOF"""
        if not query:
            return

        start_y = self.cursor_y
        start_x = self.cursor_x + 1

        pos = self.lines[start_y][start_x:].find(query)
        if pos != -1:
            self.cursor_x = start_x + pos
            self.message = f"Found '{query}'"
            self.message_type = "success"
            self.adjust_scroll()
            return

        for y in range(start_y + 1, len(self.lines)):
            pos = self.lines[y].find(query)
            if pos != -1:
                self.cursor_y = y
                self.cursor_x = pos
                self.message = f"Found '{query}'"
                self.message_type = "success"
                self.adjust_scroll()
                return

        for y in range(0, start_y):
            pos = self.lines[y].find(query)
            if pos != -1:
                self.cursor_y = y
                self.cursor_x = pos
                self.message = f"Found '{query}' (wrapped)"
                self.message_type = "success"
                self.adjust_scroll()
                return

        self.message = f"'{query}' not found"
        self.message_type = "error"

    # ------------------------------------------------------------------
    # Help and exit
    # ------------------------------------------------------------------

    def show_help(self):
        """Show help screen"""
        max_y, max_x = self.stdscr.getmaxyx()
        help_text = [
            "Atomo Help - A nano clone",
            "",
            "Main commands:",
            "  Ctrl+X  Exit (prompts to save if modified)",
            "  Ctrl+O  Save file (Write Out)",
            "  Ctrl+W  Search (Where Is)",
            "  Ctrl+K  Cut line",
            "  Ctrl+U  Paste line",
            "  Ctrl+Z  Undo (up to 200 steps)",
            "  Ctrl+G  Show this help",
            "",
            "Navigation:",
            "  Arrow Keys   Move cursor",
            "  Home/Ctrl+A  Beginning of line",
            "  End/Ctrl+E   End of line",
            "  Page Up/Down Scroll page",
            "",
            "Editing:",
            "  Enter      Insert new line",
            "  Backspace  Delete character before cursor",
            "  Delete     Delete character at cursor",
            "  Tab        Insert 4 spaces",
            "",
            "Press any key to continue...",
        ]

        self.stdscr.clear()
        for i, line in enumerate(help_text):
            if i < max_y - 1:
                self.safe_addstr(i, 2, line)

        self.stdscr.refresh()
        self.stdscr.getch()

    def confirm_exit(self) -> bool:
        """Ask user to confirm exit if buffer is modified"""
        if not self.modified:
            return True

        max_y, max_x = self.stdscr.getmaxyx()
        prompt = "Save modified buffer? (Y/N/C for cancel) "

        self.stdscr.attron(curses.color_pair(1))
        self.safe_addstr(max_y - 3, 0, " " * (max_x - 1))
        self.safe_addstr(max_y - 3, 0, prompt)
        self.stdscr.attroff(curses.color_pair(1))
        self.stdscr.refresh()

        while True:
            key = self.stdscr.getch()
            if key in [ord('y'), ord('Y')]:
                filename = self.prompt_save_filename()
                if filename and self.save_file(filename):
                    return True
                return False
            elif key in [ord('n'), ord('N'), CTRL_X]:  # Ctrl+X due volte = esci senza salvare
                return True
            elif key in [ord('c'), ord('C'), 27]:  # 27 = ESC
                return False

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        """Main editor loop"""
        while True:
            self.draw()
            key = self.stdscr.getch()

            if key == CTRL_X:
                if self.confirm_exit():
                    break

            elif key == CTRL_O:
                filename = self.prompt_save_filename()
                if filename:
                    self.save_file(filename)

            elif key == CTRL_W:
                query = self.prompt_search()
                if query:
                    self.search(query)

            elif key == CTRL_K:
                if self.lines:
                    self.push_undo()
                    self.cut_buffer = self.lines[self.cursor_y]
                    self.lines.pop(self.cursor_y)
                    if not self.lines:
                        self.lines = [""]
                    if self.cursor_y >= len(self.lines):
                        self.cursor_y = len(self.lines) - 1
                    self.cursor_x = 0
                    self.modified = True
                    self.message = "Cut line"
                    self.message_type = "info"

            elif key == CTRL_U:
                if self.cut_buffer:
                    self.push_undo()
                    self.lines.insert(self.cursor_y, self.cut_buffer)
                    self.modified = True
                    self.message = "Pasted line"
                    self.message_type = "info"

            elif key == CTRL_Z:
                self.undo()

            elif key == CTRL_G:
                self.show_help()

            elif key == CTRL_A:
                self.cursor_x = 0
                self.adjust_scroll()

            elif key == CTRL_E:
                self.cursor_x = len(self.lines[self.cursor_y])
                self.adjust_scroll()

            elif key == curses.KEY_UP:
                self.move_cursor(-1, 0)
            elif key == curses.KEY_DOWN:
                self.move_cursor(1, 0)
            elif key == curses.KEY_LEFT:
                if self.cursor_x > 0:
                    self.move_cursor(0, -1)
                elif self.cursor_y > 0:
                    self.cursor_y -= 1
                    self.cursor_x = len(self.lines[self.cursor_y])
                    self.adjust_scroll()
            elif key == curses.KEY_RIGHT:
                if self.cursor_x < len(self.lines[self.cursor_y]):
                    self.move_cursor(0, 1)
                elif self.cursor_y < len(self.lines) - 1:
                    self.cursor_y += 1
                    self.cursor_x = 0
                    self.adjust_scroll()
            elif key == curses.KEY_HOME:
                self.cursor_x = 0
                self.adjust_scroll()
            elif key == curses.KEY_END:
                self.cursor_x = len(self.lines[self.cursor_y])
                self.adjust_scroll()
            elif key == curses.KEY_PPAGE:
                height, _ = self.get_dimensions()
                self.move_cursor(-height, 0)
            elif key == curses.KEY_NPAGE:
                height, _ = self.get_dimensions()
                self.move_cursor(height, 0)

            elif key in [curses.KEY_ENTER, 10, 13]:
                self.insert_newline()

            elif key in [curses.KEY_BACKSPACE, 127, 8]:
                self.backspace()

            elif key == curses.KEY_DC:
                self.delete_char()

            elif key == 9:  # Tab
                self.insert_char('    ')

            elif 32 <= key <= 126:
                self.insert_char(chr(key))


def main(stdscr, filename: Optional[str] = None):
    """Main entry point for curses application"""
    editor = AtomoEditor(stdscr, filename)
    editor.run()


if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        curses.wrapper(main, filename)
    except KeyboardInterrupt:
        print("\nExited.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
