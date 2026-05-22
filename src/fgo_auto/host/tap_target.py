"""Target window for clicks that do not move the system cursor."""

from __future__ import annotations

from dataclasses import dataclass

_current: TapTarget | None = None


@dataclass(frozen=True)
class TapTarget:
    """Bound emulator window; frame coords match captured client (game) area."""

    hwnd: int
    origin_left: int
    origin_top: int
    client_coords: bool = True


def set_tap_target(target: TapTarget | None) -> None:
    global _current
    _current = target


def get_tap_target() -> TapTarget | None:
    return _current
