from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk
from PIL import Image, ImageTk

from fgo_auto.ui.strings_zh import translate_message


def pick_coordinate_on_capture(
    parent: tk.Misc,
    capture: Callable[[], Path],
) -> tuple[int, int] | None:
    """Capture emulator frame and return full-frame (x, y) from the user's first click."""
    try:
        path = capture()
    except Exception as exc:
        messagebox.showerror("擷圖失敗", translate_message(str(exc)), parent=parent)
        return None
    return pick_coordinate_on_image(parent, path)


def pick_coordinate_on_image(parent: tk.Misc, image_path: Path) -> tuple[int, int] | None:
    """Modal dialog: first click on the preview returns pixel coords in the full image."""
    result: list[tuple[int, int] | None] = [None]

    win = ctk.CTkToplevel(parent)
    win.title("點選座標")
    win.transient(parent.winfo_toplevel())
    win.grab_set()

    ctk.CTkLabel(
        win,
        text="在預覽圖上點一下要點擊的位置（使用第一個點的座標）。",
        wraplength=520,
    ).pack(padx=12, pady=(12, 6))

    try:
        img = Image.open(image_path).convert("RGB")
    except OSError as exc:
        messagebox.showerror("讀圖失敗", translate_message(str(exc)), parent=win)
        win.destroy()
        return None

    full_w, full_h = img.size
    thumb = img.copy()
    thumb.thumbnail((960, 540))
    thumb_w, thumb_h = thumb.size
    photo = ImageTk.PhotoImage(thumb)

    canvas = tk.Canvas(win, width=thumb_w, height=thumb_h, bg="#1a1a1a", highlightthickness=0, cursor="crosshair")
    canvas.pack(padx=12, pady=6)
    canvas.create_image(0, 0, anchor="nw", image=photo)

    coord_lbl = ctk.CTkLabel(win, text="尚未點選", anchor="w")
    coord_lbl.pack(fill="x", padx=12, pady=(0, 6))

    def on_click(event: tk.Event) -> None:
        if thumb_w <= 0 or thumb_h <= 0:
            return
        sx = full_w / thumb_w
        sy = full_h / thumb_h
        x = max(0, min(full_w - 1, int(event.x * sx)))
        y = max(0, min(full_h - 1, int(event.y * sy)))
        result[0] = (x, y)
        coord_lbl.configure(text=f"已選座標：X={x}　Y={y}")
        canvas.delete("mark")
        r = 6
        canvas.create_oval(
            event.x - r,
            event.y - r,
            event.x + r,
            event.y + r,
            outline="#ffcc00",
            width=2,
            tags="mark",
        )

    canvas.bind("<ButtonPress-1>", on_click)

    btn_row = ctk.CTkFrame(win)
    btn_row.pack(fill="x", padx=12, pady=(0, 12))

    def confirm() -> None:
        if result[0] is None:
            messagebox.showwarning("點選座標", "請先在預覽圖上點一下。", parent=win)
            return
        win.grab_release()
        win.destroy()

    def cancel() -> None:
        result[0] = None
        win.grab_release()
        win.destroy()

    ctk.CTkButton(btn_row, text="確定", width=72, command=confirm).pack(side="left", padx=(0, 8))
    ctk.CTkButton(btn_row, text="取消", width=72, fg_color="#555555", command=cancel).pack(side="left")

    win._photo = photo  # type: ignore[attr-defined]
    win.wait_window()
    return result[0]
