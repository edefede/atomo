#!/usr/bin/env python3
"""
Atomo - A nano clone text editor in Python
Usage: python atomo.py [filename]
"""

import curses
import sys
import os
from typing import List, Optional, Tuple


class AtomoEditor:
    """Main editor class that handles the text editing interface"""

    def __init__(self, stdscr, filename: Optional[str] = None):
        self.stdscr = stdscr
        self.filename = filename
        self.lines: List[str] = []
        self.cursor_y = 0
        self.cursor_x = 0
        self.offset_y = 0  # Scroll offset for vertical scrolling
        self.offset_x = 0  # Scroll offset for horizontal scrolling
        self.modified = False
        self.message = ""
        self.message_type = "info"  # info, error, success

        # Initialize colors
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Status bar
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE)   # Title bar
        curses.init_pair(3, curses.COLOR_RED, -1)                    # Error
        curses.init_pair(4, curses.COLOR_GREEN, -1)                  # Success

        # Configure curses
        curses.curs_set(1)  # Show cursor
        self.stdscr.keypad(True)

        # Load file if specified
        if filename:
            self.load_file(filename)
        else:
            self.lines = [""]

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
                f.write('\n'.join(self.lines))
                if self.lines and self.lines[-1]:  # Add final newline if last line has content
                    f.write('\n')

            self.modified = False
            self.message = f'Wrote {len(self.lines)} lines to {self.filename}'
            self.message_type = "success"
            return True
        except Exception as e:
            self.message = f'Error writing {self.filename}: {str(e)}'
            self.message_type = "error"
            return False

    def get_dimensions(self) -> Tuple[int, int]:
        """Get usable dimensions (excluding status bars)"""
        max_y, max_x = self.stdscr.getmaxyx()
        # Reserve 2 lines for title and 2 lines for status/help
        return max_y - 4, max_x

    def safe_addstr(self, y, x, text, attr=0):
        """Safely add string to screen with error handling"""
        max_y, max_x = self.stdscr.getmaxyx()
        if y >= max_y or x >= max_x:
            return

        # Truncate text to fit
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
            pass  # Ignore curses errors (usually at screen edge)

    def draw_title_bar(self):
        """Draw the top title bar"""
        max_y, max_x = self.stdscr.getmaxyx()
        title = "  GNU nano clone - Atomo"
        filename_display = self.filename if self.filename else "[New Buffer]"

        # Modified indicator
        mod_indicator = " *" if self.modified else ""

        self.stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
        self.safe_addstr(0, 0, " " * (max_x - 1))
        self.safe_addstr(0, 0, title)

        # Show filename in the center
        filename_str = f" File: {filename_display}{mod_indicator} "
        if len(filename_str) < max_x - len(title):
            x_pos = (max_x - len(filename_str)) // 2
            self.safe_addstr(0, x_pos, filename_str)

        self.stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

    def draw_status_bar(self):
        """Draw the bottom status bar"""
        max_y, max_x = self.stdscr.getmaxyx()

        # Line and column info
        status_left = f" Line {self.cursor_y + 1}/{len(self.lines)}  Col {self.cursor_x + 1} "

        self.stdscr.attron(curses.color_pair(1))
        self.safe_addstr(max_y - 2, 0, " " * (max_x - 1))
        self.safe_addstr(max_y - 2, 0, status_left)
        self.stdscr.attroff(curses.color_pair(1))

    def draw_help_bar(self):
        """Draw the bottom help bar with shortcuts"""
        max_y, max_x = self.stdscr.getmaxyx()

        shortcuts = [
            ("^X", "Exit"), ("^O", "Save"), ("^W", "Where Is"),
            ("^K", "Cut"), ("^U", "Paste"), ("^G", "Help")
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

            # Clear the line
            self.safe_addstr(max_y - 3, 0, " " * (max_x - 1))
            self.stdscr.attron(color | curses.A_BOLD)
            self.safe_addstr(max_y - 3, 0, f" {self.message}")
            self.stdscr.attroff(color | curses.A_BOLD)

    def draw_buffer(self):
        """Draw the text buffer"""
        height, width = self.get_dimensions()

        for screen_y in range(height):
            buffer_y = screen_y + self.offset_y

            # Clear the line
            self.safe_addstr(screen_y + 1, 0, " " * width)

            if buffer_y < len(self.lines):
                line = self.lines[buffer_y]
                # Apply horizontal scrolling
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

        # Position cursor
        screen_y = self.cursor_y - self.offset_y + 1
        screen_x = self.cursor_x - self.offset_x
        height, width = self.get_dimensions()

        if 0 <= screen_y < height + 1 and 0 <= screen_x < width:
            self.stdscr.move(screen_y, screen_x)

        self.stdscr.refresh()

    def adjust_scroll(self):
        """Adjust scroll offsets to keep cursor visible"""
        height, width = self.get_dimensions()

        # Vertical scrolling
        if self.cursor_y < self.offset_y:
            self.offset_y = self.cursor_y
        elif self.cursor_y >= self.offset_y + height:
            self.offset_y = self.cursor_y - height + 1

        # Horizontal scrolling
        if self.cursor_x < self.offset_x:
            self.offset_x = self.cursor_x
        elif self.cursor_x >= self.offset_x + width:
            self.offset_x = self.cursor_x - width + 1

    def move_cursor(self, dy: int, dx: int):
        """Move cursor with bounds checking"""
        # Clear message when moving cursor
        self.message = ""

        self.cursor_y = max(0, min(len(self.lines) - 1, self.cursor_y + dy))

        # Horizontal movement
        current_line = self.lines[self.cursor_y]
        self.cursor_x = max(0, min(len(current_line), self.cursor_x + dx))

        self.adjust_scroll()

    def insert_char(self, char: str):
        """Insert a character at cursor position"""
        line = self.lines[self.cursor_y]
        self.lines[self.cursor_y] = line[:self.cursor_x] + char + line[self.cursor_x:]
        self.cursor_x += 1
        self.modified = True
        self.message = ""
        self.adjust_scroll()

    def delete_char(self):
        """Delete character at cursor (Delete key)"""
        line = self.lines[self.cursor_y]

        if self.cursor_x < len(line):
            # Delete character at cursor
            self.lines[self.cursor_y] = line[:self.cursor_x] + line[self.cursor_x + 1:]
            self.modified = True
        elif self.cursor_y < len(self.lines) - 1:
            # At end of line, merge with next line
            self.lines[self.cursor_y] = line + self.lines[self.cursor_y + 1]
            self.lines.pop(self.cursor_y + 1)
            self.modified = True

        self.message = ""

    def backspace(self):
        """Delete character before cursor (Backspace key)"""
        if self.cursor_x > 0:
            line = self.lines[self.cursor_y]
            self.lines[self.cursor_y] = line[:self.cursor_x - 1] + line[self.cursor_x:]
            self.cursor_x -= 1
            self.modified = True
        elif self.cursor_y > 0:
            # At beginning of line, merge with previous line
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
        line = self.lines[self.cursor_y]
        # Split the current line
        self.lines[self.cursor_y] = line[:self.cursor_x]
        self.lines.insert(self.cursor_y + 1, line[self.cursor_x:])
        self.cursor_y += 1
        self.cursor_x = 0
        self.modified = True
        self.message = ""
        self.adjust_scroll()

    def prompt_save_filename(self) -> Optional[str]:
        """Prompt user for filename to save"""
        max_y, max_x = self.stdscr.getmaxyx()
        prompt = f"File Name to Write: {self.filename if self.filename else ''}"

        # Show prompt
        self.stdscr.attron(curses.color_pair(1))
        self.safe_addstr(max_y - 3, 0, " " * (max_x - 1))
        self.safe_addstr(max_y - 3, 0, prompt)
        self.stdscr.attroff(curses.color_pair(1))

        # Get input
        curses.echo()
        try:
            self.stdscr.move(max_y - 3, min(len(prompt), max_x - 2))
            input_str = self.stdscr.getstr(max_y - 3, min(len(prompt), max_x - 2), max(1, max_x - len(prompt) - 1)).decode('utf-8')
        except:
            input_str = ""
        curses.noecho()

        if input_str.strip():
            return input_str.strip()
        return self.filename

    def prompt_search(self) -> Optional[str]:
        """Prompt user for search text"""
        max_y, max_x = self.stdscr.getmaxyx()
        prompt = "Search: "

        # Show prompt
        self.stdscr.attron(curses.color_pair(1))
        self.safe_addstr(max_y - 3, 0, " " * (max_x - 1))
        self.safe_addstr(max_y - 3, 0, prompt)
        self.stdscr.attroff(curses.color_pair(1))

        # Get input
        curses.echo()
        try:
            self.stdscr.move(max_y - 3, min(len(prompt), max_x - 2))
            input_str = self.stdscr.getstr(max_y - 3, min(len(prompt), max_x - 2), max(1, max_x - len(prompt) - 1)).decode('utf-8')
        except:
            input_str = ""
        curses.noecho()

        return input_str.strip() if input_str.strip() else None

    def search(self, query: str):
        """Search for text in buffer"""
        if not query:
            return

        # Search from current position
        start_y = self.cursor_y
        start_x = self.cursor_x + 1

        # Search current line first (from cursor position)
        pos = self.lines[start_y][start_x:].find(query)
        if pos != -1:
            self.cursor_x = start_x + pos
            self.message = f"Found '{query}'"
            self.message_type = "success"
            self.adjust_scroll()
            return

        # Search remaining lines
        for y in range(start_y + 1, len(self.lines)):
            pos = self.lines[y].find(query)
            if pos != -1:
                self.cursor_y = y
                self.cursor_x = pos
                self.message = f"Found '{query}'"
                self.message_type = "success"
                self.adjust_scroll()
                return

        # Wrap around and search from beginning
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
            "  Ctrl+G  Show this help",
            "",
            "Navigation:",
            "  Arrow Keys  Move cursor",
            "  Home/Ctrl+A Beginning of line",
            "  End/Ctrl+E  End of line",
            "  Page Up/Down Scroll page",
            "",
            "Editing:",
            "  Enter      Insert new line",
            "  Backspace  Delete character before cursor",
            "  Delete     Delete character at cursor",
            "",
            "Press any key to continue..."
        ]

        self.stdscr.clear()
        for i, line in enumerate(help_text):
            if i < max_y - 1:
                self.safe_addstr(i, 2, line)

        self.stdscr.refresh()
        self.stdscr.getch()

    def confirm_exit(self) -> bool:
        """Ask user to confirm exit if modified"""
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
                # Save and exit
                filename = self.prompt_save_filename()
                if filename and self.save_file(filename):
                    return True
                return False
            elif key in [ord('n'), ord('N')]:
                # Exit without saving
                return True
            elif key in [ord('c'), ord('C'), 27]:  # 27 is ESC
                # Cancel
                return False

    def run(self):
        """Main editor loop"""
        cut_buffer = ""

        while True:
            self.draw()
            key = self.stdscr.getch()

            # Handle Ctrl+X (Exit)
            if key == 24:  # Ctrl+X
                if self.confirm_exit():
                    break

            # Handle Ctrl+O (Save)
            elif key == 15:  # Ctrl+O
                filename = self.prompt_save_filename()
                if filename:
                    self.save_file(filename)

            # Handle Ctrl+W (Search)
            elif key == 23:  # Ctrl+W
                query = self.prompt_search()
                if query:
                    self.search(query)

            # Handle Ctrl+K (Cut line)
            elif key == 11:  # Ctrl+K
                if self.lines:
                    cut_buffer = self.lines[self.cursor_y]
                    self.lines.pop(self.cursor_y)
                    if not self.lines:
                        self.lines = [""]
                    if self.cursor_y >= len(self.lines):
                        self.cursor_y = len(self.lines) - 1
                    self.cursor_x = 0
                    self.modified = True
                    self.message = "Cut line"
                    self.message_type = "info"

            # Handle Ctrl+U (Paste)
            elif key == 21:  # Ctrl+U
                if cut_buffer:
                    self.lines.insert(self.cursor_y, cut_buffer)
                    self.modified = True
                    self.message = "Pasted line"
                    self.message_type = "info"

            # Handle Ctrl+G (Help)
            elif key == 7:  # Ctrl+G
                self.show_help()

            # Handle Ctrl+A (Home)
            elif key == 1:  # Ctrl+A
                self.cursor_x = 0
                self.adjust_scroll()

            # Handle Ctrl+E (End)
            elif key == 5:  # Ctrl+E
                self.cursor_x = len(self.lines[self.cursor_y])
                self.adjust_scroll()

            # Navigation keys
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
            elif key == curses.KEY_PPAGE:  # Page Up
                height, _ = self.get_dimensions()
                self.move_cursor(-height, 0)
            elif key == curses.KEY_NPAGE:  # Page Down
                height, _ = self.get_dimensions()
                self.move_cursor(height, 0)

            # Handle Enter
            elif key in [curses.KEY_ENTER, 10, 13]:
                self.insert_newline()

            # Handle Backspace
            elif key in [curses.KEY_BACKSPACE, 127, 8]:
                self.backspace()

            # Handle Delete
            elif key == curses.KEY_DC:
                self.delete_char()

            # Handle Tab
            elif key == 9:
                self.insert_char('    ')  # Insert 4 spaces

            # Handle printable characters
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
