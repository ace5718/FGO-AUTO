from __future__ import annotations

import ctypes
from ctypes import wintypes

from fgo_auto.host.window_binder import WindowBinder, WindowBindingError, WindowInfo, _matches_rule


class Win32WindowBinder(WindowBinder):
    def list_windows(self) -> list[WindowInfo]:
        user32 = ctypes.windll.user32
        results: list[WindowInfo] = []

        def callback(hwnd: int, _lparam: int) -> bool:
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            title = buffer.value
            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            if width > 0 and height > 0:
                results.append(
                    WindowInfo(
                        handle=hwnd,
                        title=title,
                        left=rect.left,
                        top=rect.top,
                        width=width,
                        height=height,
                    )
                )
            return True

        enum_func = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(callback)
        user32.EnumWindows(enum_func, 0)
        return results

    def resolve(self, title_rule: str, *, pick_handle: int | None = None) -> WindowInfo:
        matches = [w for w in self.list_windows() if _matches_rule(w.title, title_rule)]
        if pick_handle is not None:
            for window in matches:
                if window.handle == pick_handle:
                    return window
            raise WindowBindingError(f"No window with handle {pick_handle} matched rule")
        if not matches:
            raise WindowBindingError(f"No window matched title rule: {title_rule!r}")
        if len(matches) > 1:
            lines = "\n".join(f"  [{i + 1}] handle={w.handle} title={w.title!r}" for i, w in enumerate(matches))
            raise WindowBindingError(
                f"Multiple windows ({len(matches)}) matched rule {title_rule!r}:\n{lines}\n"
                "Re-run with Window pick (fgo-auto window-pick)."
            )
        return matches[0]
