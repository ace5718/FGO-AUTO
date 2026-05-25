from __future__ import annotations

import structlog

from fgo_auto.host.tap_target import get_tap_target

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

    from fgo_auto.host.input_backend import active_input_method, adb_client

    if active_input_method() == "adb":
        client = adb_client()
        if client is not None:
            client.tap(coords[0], coords[1])
            return

    target = get_tap_target()
    if sys.platform == "win32" and target is not None:
        from fgo_auto.host.window_click import post_click

        post_click(target, coords[0], coords[1])
        return

    if sys.platform == "win32":
        logger.error(
            "tap_no_window_bound",
            x=coords[0],
            y=coords[1],
            hint="Bind BlueStacks on the Run tab before starting",
        )
        return
    logger.info("click_simulated", x=coords[0], y=coords[1])


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

    from fgo_auto.host.input_backend import active_input_method, adb_client

    if active_input_method() == "adb":
        client = adb_client()
        if client is not None:
            client.swipe(
                start[0],
                start[1],
                end[0],
                end[1],
                duration_ms=int(duration_s * 1000),
            )
            return

    target = get_tap_target()
    if sys.platform == "win32" and target is not None:
        from fgo_auto.host.window_click import post_swipe

        post_swipe(target, start, end, duration_s=duration_s)
        return

    if sys.platform == "win32":
        logger.error(
            "swipe_no_window_bound",
            start=start,
            end=end,
            hint="Bind BlueStacks on the Run tab before starting",
        )
        return
    logger.info("swipe_simulated", start=start, end=end)
