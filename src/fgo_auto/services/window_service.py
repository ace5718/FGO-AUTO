from __future__ import annotations

from dataclasses import dataclass

from fgo_auto.host.window_binder import (
    WindowBinder,
    WindowBindingError,
    WindowInfo,
    _matches_rule,
    create_window_binder,
)


@dataclass(frozen=True)
class WindowCandidate:
    handle: int
    title: str
    width: int
    height: int


class WindowService:
    def __init__(self, binder: WindowBinder | None = None) -> None:
        self._binder = binder or create_window_binder()

    def list_matching(self, title_rule: str) -> list[WindowCandidate]:
        matches = [
            WindowCandidate(w.handle, w.title, w.width, w.height)
            for w in self._binder.list_windows()
            if _matches_rule(w.title, title_rule)
        ]
        return matches

    def resolve(self, title_rule: str, pick_handle: int | None = None) -> WindowInfo:
        return self._binder.resolve(title_rule, pick_handle=pick_handle)


__all__ = ["WindowService", "WindowCandidate", "WindowBindingError"]
