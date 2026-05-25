"""Capture window client pixels without picking up overlapping desktop UI."""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

import numpy as np

PW_RENDERFULLCONTENT = 2
SRCCOPY = 0x00CC0020
DIB_RGB_COLORS = 0
BI_RGB = 0


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


def _user32():
    return ctypes.windll.user32


def _gdi32():
    return ctypes.windll.gdi32


def _window_title(hwnd: int) -> str:
    user32 = _user32()
    length = user32.GetWindowTextLengthW(hwnd) + 1
    if length <= 1:
        return ""
    buf = ctypes.create_unicode_buffer(length)
    user32.GetWindowTextW(hwnd, buf, length)
    return buf.value


def resolve_input_hwnd(top_hwnd: int) -> int:
    """
    HWND that accepts injected mouse messages (BlueStacks: PluginAndroid child).
    Falls back to the largest visible child used for capture.
    """
    if sys.platform != "win32":
        return top_hwnd

    user32 = _user32()
    plugin_handles: list[int] = []

    def visit(parent: int) -> None:
        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def callback(child: int, _lparam: int) -> bool:
            title = _window_title(child)
            if "PluginAndroid" in title:
                plugin_handles.append(child)
            visit(child)
            return True

        user32.EnumChildWindows(parent, callback, 0)

    visit(top_hwnd)
    if plugin_handles:
        return plugin_handles[0]
    return resolve_capture_hwnd(top_hwnd)


def resolve_capture_hwnd(top_hwnd: int) -> int:
    """
    Prefer the largest visible child (BlueStacks render surface); else top-level hwnd.
    """
    if sys.platform != "win32":
        return top_hwnd

    user32 = _user32()
    best = top_hwnd
    best_area = 0
    client = wintypes.RECT()
    if user32.GetClientRect(top_hwnd, ctypes.byref(client)):
        best_area = int((client.right - client.left) * (client.bottom - client.top))

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def callback(child: int, _lparam: int) -> bool:
        nonlocal best, best_area
        if not user32.IsWindowVisible(child):
            return True
        rect = wintypes.RECT()
        if not user32.GetClientRect(child, ctypes.byref(rect)):
            return True
        w = rect.right - rect.left
        h = rect.bottom - rect.top
        area = int(w * h)
        if area > best_area:
            best_area = area
            best = child
        return True

    user32.EnumChildWindows(top_hwnd, callback, 0)
    return best


def capture_hwnd_bgr(hwnd: int, width: int, height: int) -> np.ndarray | None:
    """Return BGR image from window backing store, or None if GDI capture failed."""
    if sys.platform != "win32" or width <= 0 or height <= 0:
        return None

    user32 = _user32()
    gdi32 = _gdi32()
    hwnd_dc = user32.GetDC(hwnd)
    if not hwnd_dc:
        return None
    mem_dc = gdi32.CreateCompatibleDC(hwnd_dc)
    bitmap = gdi32.CreateCompatibleBitmap(hwnd_dc, width, height)
    old = gdi32.SelectObject(mem_dc, bitmap)
    try:
        ok = user32.PrintWindow(hwnd, mem_dc, PW_RENDERFULLCONTENT)
        if not ok:
            ok = user32.PrintWindow(hwnd, mem_dc, 0)
        if not ok:
            ok = gdi32.BitBlt(mem_dc, 0, 0, width, height, hwnd_dc, 0, 0, SRCCOPY)

        if not ok:
            return None

        header = BITMAPINFOHEADER()
        header.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        header.biWidth = width
        header.biHeight = -height
        header.biPlanes = 1
        header.biBitCount = 24
        header.biCompression = BI_RGB
        info = BITMAPINFO()
        info.bmiHeader = header

        # Each DIB scanline is padded to a 4-byte boundary. Compute stride and
        # allocate buffer accordingly, then rebuild a (H, W, 3) array by
        # stripping the padding bytes per row.
        line_bytes = ((width * 3 + 3) // 4) * 4
        buf_size = line_bytes * height
        buf = (ctypes.c_char * buf_size)()
        lines = gdi32.GetDIBits(mem_dc, bitmap, 0, height, buf, ctypes.byref(info), DIB_RGB_COLORS)
        if not lines:
            return None

        arr = np.frombuffer(buf, dtype=np.uint8)
        if arr.size != buf_size:
            # Unexpected size — fail safe
            return None
        arr = arr.reshape((height, line_bytes))
        # Keep only the first width*3 bytes of each row (drop padding), then
        # reshape to (height, width, 3).
        arr = arr[:, : width * 3].reshape((height, width, 3)).copy()
        return arr
    finally:
        gdi32.SelectObject(mem_dc, old)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(mem_dc)
        user32.ReleaseDC(hwnd, hwnd_dc)
