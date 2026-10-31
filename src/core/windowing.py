"""Best-effort helpers for interacting with other top-level windows (Windows)."""
from __future__ import annotations

import ctypes
import os
from ctypes import wintypes

_SW_RESTORE = 9


def focus_window_for_pid(pid: int) -> bool:
    """Bring the first visible top-level window of ``pid`` to the foreground.

    Used when the user double-clicks a card whose tool is already running.
    Returns False on non-Windows platforms or when no window is found.
    """
    if os.name != "nt":
        return False
    try:
        user32 = ctypes.windll.user32
    except (AttributeError, OSError):
        return False

    found: list[int] = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def _enum_proc(hwnd, _lparam):  # noqa: ANN001 - ctypes callback
        pid_ref = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_ref))
        if (
            pid_ref.value == pid
            and user32.IsWindowVisible(hwnd)
            and user32.GetWindowTextLengthW(hwnd) > 0
        ):
            found.append(hwnd)
            return False  # stop at first match
        return True

    try:
        user32.EnumWindows(_enum_proc, 0)
    except OSError:
        return False

    if not found:
        return False
    hwnd = found[0]
    try:
        user32.ShowWindow(hwnd, _SW_RESTORE)
        user32.SetForegroundWindow(hwnd)
    except OSError:
        return False
    return True
