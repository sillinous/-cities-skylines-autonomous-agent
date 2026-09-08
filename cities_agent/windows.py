from __future__ import annotations

from dataclasses import dataclass
import ctypes
from ctypes import wintypes


@dataclass(frozen=True)
class WindowInfo:
    handle: int
    title: str
    visible: bool


class WindowsGameWindow:
    """Small Windows-only adapter for detecting and validating the game window."""

    def __init__(self, title_tokens: tuple[str, ...] = ("cities: skylines", "cities skylines")):
        self.title_tokens = tuple(token.lower() for token in title_tokens)

    def enumerate(self) -> tuple[WindowInfo, ...]:
        if not hasattr(ctypes, "windll"):
            return ()
        user32 = ctypes.windll.user32
        windows: list[WindowInfo] = []

        @wintypes.BOOL
        def callback(hwnd, _lparam):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                buffer = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buffer, length + 1)
                windows.append(WindowInfo(int(hwnd), buffer.value, True))
            return True

        user32.EnumWindows(callback, 0)
        return tuple(windows)

    def find_game(self) -> WindowInfo | None:
        for window in self.enumerate():
            title = window.title.lower()
            if any(token in title for token in self.title_tokens):
                return window
        return None

    def game_detected(self) -> bool:
        return self.find_game() is not None

    def is_foreground(self) -> bool:
        game = self.find_game()
        if game is None or not hasattr(ctypes, "windll"):
            return False
        return int(ctypes.windll.user32.GetForegroundWindow()) == game.handle

    def resolution(self) -> tuple[int, int] | None:
        game = self.find_game()
        if game is None or not hasattr(ctypes, "windll"):
            return None
        rect = wintypes.RECT()
        if not ctypes.windll.user32.GetWindowRect(game.handle, ctypes.byref(rect)):
            return None
        return max(0, rect.right - rect.left), max(0, rect.bottom - rect.top)
