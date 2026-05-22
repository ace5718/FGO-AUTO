from __future__ import annotations

import structlog

logger = structlog.get_logger()


def normalized_to_pixels(
    x: float,
    y: float,
    width: int,
    height: int,
) -> tuple[int, int]:
    """Convert 0–1 normalized coords to pixel coordinates."""
    x_clamped = min(max(float(x), 0.0), 1.0)
    y_clamped = min(max(float(y), 0.0), 1.0)
    return int(x_clamped * width), int(y_clamped * height)


def tap_pixels(coords: tuple[int, int]) -> None:
    import sys

    if sys.platform != "win32":
        logger.info("click_simulated", x=coords[0], y=coords[1])
        return
    try:
        import pyautogui
    except ImportError:
        logger.warning("pyautogui_missing", x=coords[0], y=coords[1])
        return
    pyautogui.click(coords[0], coords[1])


def tap_normalized(x: float, y: float, width: int, height: int) -> None:
    tap_pixels(normalized_to_pixels(x, y, width, height))


def swipe_pixels(
    start: tuple[int, int],
    end: tuple[int, int],
    *,
    duration_s: float = 0.35,
) -> None:
    """Drag on screen (e.g. scroll a vertical quest list)."""
    import sys

    if sys.platform != "win32":
        logger.info("swipe_simulated", start=start, end=end)
        return
    try:
        import pyautogui
    except ImportError:
        logger.warning("pyautogui_missing", start=start, end=end)
        return
    pyautogui.moveTo(start[0], start[1])
    pyautogui.dragTo(end[0], end[1], duration=duration_s, button="left")
    logger.info("swipe", start=start, end=end)
