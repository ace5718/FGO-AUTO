from __future__ import annotations

import tkinter as tk
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageTk

from fgo_auto.services.quest_flow_service import anchor_png_path


def _pil_anchor_image(path: Path) -> Image.Image:
    img = Image.open(path)
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (32, 32, 32))
        bg.paste(img, mask=img.split()[3])
        return bg
    return img.convert("RGB")


def show_anchor_fullsize(master, profile_dir: Path | None, name: str, resolution: str | None = None) -> None:
    """Open a dialog with the full anchor PNG (click thumbnail in flow steps)."""
    if profile_dir is None:
        return
    path = anchor_png_path(profile_dir, name, resolution)
    if path is None:
        return

    win = ctk.CTkToplevel(master)
    win.title(f"圖示：{name}")
    win.geometry("720x520")
    win.transient(master.winfo_toplevel())

    img = _pil_anchor_image(path)
    max_w, max_h = 680, 440
    scale = min(max_w / img.width, max_h / img.height, 1.0)
    disp = img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(disp)

    ctk.CTkLabel(win, text=f"{name}　（{path.name}）", anchor="w").pack(fill="x", padx=12, pady=(12, 4))
    frame = ctk.CTkFrame(win)
    frame.pack(fill="both", expand=True, padx=12, pady=4)
    lbl = tk.Label(frame, image=photo, bg="#2a2a2a", cursor="arrow")
    lbl.image = photo  # keep reference
    lbl.pack(padx=8, pady=8)
    ctk.CTkLabel(win, text="點縮圖可隨時開啟此視窗", text_color="#888888").pack(pady=(0, 8))
    ctk.CTkButton(win, text="關閉", width=80, command=win.destroy).pack(pady=(0, 12))
