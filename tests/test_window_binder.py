import pytest

from fgo_auto.host.window_binder import InMemoryWindowBinder, WindowBindingError, WindowInfo


def test_resolve_single_match() -> None:
    windows = [
        WindowInfo(1, "BlueStacks App Player", 0, 0, 1920, 1080),
        WindowInfo(2, "Other App", 0, 0, 800, 600),
    ]
    binder = InMemoryWindowBinder(windows)
    window = binder.resolve("BlueStacks")
    assert window.handle == 1


def test_multiple_matches_raises() -> None:
    windows = [
        WindowInfo(1, "BlueStacks 1", 0, 0, 1920, 1080),
        WindowInfo(2, "BlueStacks 2", 0, 0, 1920, 1080),
    ]
    binder = InMemoryWindowBinder(windows)
    with pytest.raises(WindowBindingError, match="Multiple windows"):
        binder.resolve("BlueStacks")


def test_pick_handle_selects_one() -> None:
    windows = [
        WindowInfo(1, "BlueStacks 1", 0, 0, 1920, 1080),
        WindowInfo(2, "BlueStacks 2", 0, 0, 1920, 1080),
    ]
    binder = InMemoryWindowBinder(windows)
    window = binder.resolve("BlueStacks", pick_handle=2)
    assert window.handle == 2
