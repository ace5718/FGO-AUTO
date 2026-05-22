from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol


class WindowBindingError(Exception):
    """Window binding failed."""


@dataclass(frozen=True)
class WindowInfo:
    handle: int
    title: str
    left: int
    top: int
    width: int
    height: int


class WindowBinder(Protocol):
    def list_windows(self) -> list[WindowInfo]: ...

    def resolve(self, title_rule: str, *, pick_handle: int | None = None) -> WindowInfo:
        """Resolve exactly one window, or raise WindowBindingError."""


def _matches_rule(title: str, rule: str) -> bool:
    if rule.startswith("re:"):
        pattern = rule[3:]
        return re.search(pattern, title) is not None
    return rule.lower() in title.lower()


class InMemoryWindowBinder:
    """Test double with injectable window list."""

    def __init__(self, windows: list[WindowInfo]) -> None:
        self._windows = windows

    def list_windows(self) -> list[WindowInfo]:
        return list(self._windows)

    def resolve(self, title_rule: str, *, pick_handle: int | None = None) -> WindowInfo:
        matches = [w for w in self._windows if _matches_rule(w.title, title_rule)]
        if pick_handle is not None:
            for window in matches:
                if window.handle == pick_handle:
                    return window
            raise WindowBindingError(f"No window with handle {pick_handle} matched rule")
        if not matches:
            raise WindowBindingError(f"No window matched title rule: {title_rule!r}")
        if len(matches) > 1:
            titles = ", ".join(f"{w.handle}:{w.title!r}" for w in matches)
            raise WindowBindingError(
                f"Multiple windows ({len(matches)}) matched rule {title_rule!r}: {titles}. "
                "Use Window pick or narrow window_title_rule."
            )
        return matches[0]


def create_window_binder() -> WindowBinder:
    import sys

    if sys.platform == "win32":
        from fgo_auto.host.win32 import Win32WindowBinder

        return Win32WindowBinder()
    return InMemoryWindowBinder([])
