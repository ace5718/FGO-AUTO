from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Callable

import customtkinter as ctk
from PIL import Image, ImageTk

from fgo_auto.services.quest_flow_service import anchor_png_path

_GALLERY_CELL = (160, 100)


def _pil_anchor_image(path: Path) -> Image.Image:
    img = Image.open(path)
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (48, 48, 48))
        bg.paste(img, mask=img.split()[3])
        return bg
    return img.convert("RGB")


def _photo_for_path(path: Path, size: tuple[int, int]) -> ImageTk.PhotoImage:
    img = _pil_anchor_image(path)
    img.thumbnail(size, Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(img)


class AnchorGalleryPanel(ctk.CTkScrollableFrame):
    """Grid of anchor PNG previews; click to assign to the active step."""

    def __init__(
        self,
        master,
        on_pick: Callable[[str], None],
        **kwargs,
    ) -> None:
        super().__init__(master, label_text="圖示庫（點圖選入目前步驟）", height=200, **kwargs)
        self._on_pick = on_pick
        self._profile_dir: Path | None = None
        self._names: list[str] = []
        self._photos: list[ImageTk.PhotoImage] = []
        self._selected: str | None = None
        self._grid = ctk.CTkFrame(self)
        self._grid.pack(fill="both", expand=True, padx=4, pady=4)
        self._hint = ctk.CTkLabel(self, text="請先點某一列步驟的「選圖示」", text_color="#aaaaaa")
        self._hint.pack(anchor="w", padx=8, pady=(0, 4))

    def load(self, profile_dir: Path | None, names: list[str], *, selected: str | None = None) -> None:
        self._profile_dir = profile_dir
        self._names = [n for n in names if not n.startswith("（")]
        self._selected = selected
        for child in self._grid.winfo_children():
            child.destroy()
        self._photos.clear()
        if not self._names or profile_dir is None:
            ctk.CTkLabel(self._grid, text="尚無圖示，請到「預覽」擷圖並儲存框選。").pack(padx=8, pady=12)
            return
        cols = 4
        for i, name in enumerate(self._names):
            path = anchor_png_path(profile_dir, name)
            cell = ctk.CTkFrame(self._grid, fg_color="#333333" if name == selected else "#2a2a2a", corner_radius=6)
            cell.grid(row=i // cols, column=i % cols, padx=6, pady=6, sticky="n")
            if path:
                photo = _photo_for_path(path, _GALLERY_CELL)
                self._photos.append(photo)
                img_lbl = tk.Label(cell, image=photo, bg="#2a2a2a", cursor="hand2")
                img_lbl.pack(padx=4, pady=(4, 0))
                img_lbl.bind("<Button-1>", lambda _e, n=name: self._pick(n))
            else:
                tk.Label(cell, text="無檔", width=18, height=6, bg="#2a2a2a", fg="#888").pack(padx=4, pady=8)
            btn = ctk.CTkButton(
                cell,
                text=name,
                width=150,
                height=22,
                font=ctk.CTkFont(size=11),
                fg_color="#1f538d" if name == selected else "#3a3a3a",
                command=lambda n=name: self._pick(n),
            )
            btn.pack(padx=4, pady=(2, 6))
            if name == selected:
                cell.configure(fg_color="#1a4a7a")

    def set_pick_hint(self, text: str) -> None:
        self._hint.configure(text=text)

    def _pick(self, name: str) -> None:
        self._selected = name
        self.load(self._profile_dir, self._names, selected=name)
        self._on_pick(name)

    def highlight(self, name: str | None) -> None:
        self.load(self._profile_dir, self._names, selected=name)
