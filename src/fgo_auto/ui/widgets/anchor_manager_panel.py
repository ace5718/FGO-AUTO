from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Callable

import customtkinter as ctk
from PIL import Image, ImageTk

from fgo_auto.quest.models import NavigationScript, QuestProfile
from fgo_auto.services.quest_flow_service import (
    anchor_png_path,
    anchors_referenced_by_flow,
    delete_quest_anchor,
    list_saved_anchors,
    list_shared_anchors,
    shared_anchors_dir,
)
from fgo_auto.ui.widgets.anchor_preview_dialog import show_anchor_fullsize

_CELL = (72, 48)


def _thumb_photo(path: Path) -> ImageTk.PhotoImage | None:
    try:
        img = Image.open(path)
        if img.mode == "RGBA":
            bg = Image.new("RGB", img.size, (48, 48, 48))
            bg.paste(img, mask=img.split()[3])
            img = bg
        else:
            img = img.convert("RGB")
        img.thumbnail(_CELL, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except OSError:
        return None


class AnchorManagerPanel(ctk.CTkFrame):
    """List quest anchor PNGs; preview and delete."""

    def __init__(
        self,
        master,
        *,
        on_changed: Callable[[], None] | None = None,
        shared_mode: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_changed = on_changed
        self._shared_mode = shared_mode
        self._profile_dir: Path | None = None
        self._editable = False
        self._profile: QuestProfile | None = None
        self._navigation: NavigationScript | None = None
        self._photos: list[ImageTk.PhotoImage] = []

        self._grid_host = ctk.CTkScrollableFrame(self, height=360, label_text="")
        self._grid_host.pack(fill="both", expand=True, padx=8, pady=4)

        self._empty_lbl = ctk.CTkLabel(
            self._grid_host,
            text="尚無圖示。請到「預覽」擷圖並儲存框選。",
            anchor="w",
        )

    def load_shared(self, *, editable: bool) -> None:
        self._shared_mode = True
        self._profile_dir = None
        self._profile = None
        self._navigation = None
        self._editable = editable
        self._refresh()

    def load(
        self,
        profile_dir: Path | None,
        *,
        editable: bool,
        profile: QuestProfile | None = None,
        navigation: NavigationScript | None = None,
    ) -> None:
        self._shared_mode = False
        self._profile_dir = profile_dir
        self._editable = editable
        self._profile = profile
        self._navigation = navigation
        self._refresh()

    def _refresh(self) -> None:
        for child in self._grid_host.winfo_children():
            child.destroy()
        self._photos.clear()

        if self._shared_mode:
            names = list_shared_anchors()
        elif self._profile_dir is None:
            ctk.CTkLabel(self._grid_host, text="請先選關卡").pack(padx=8, pady=8)
            return
        else:
            names = list_saved_anchors(self._profile_dir)
        if not names:
            self._empty_lbl = ctk.CTkLabel(
                self._grid_host,
                text="尚無圖示。請到「預覽」擷圖並儲存框選。",
                anchor="w",
            )
            self._empty_lbl.pack(padx=8, pady=8)
            return

        in_use: set[str] = set()
        if self._profile and self._navigation:
            in_use = anchors_referenced_by_flow(self._profile, self._navigation)

        cols = 5
        for i, name in enumerate(names):
            path = (
                shared_anchors_dir() / f"{name}.png"
                if self._shared_mode
                else anchor_png_path(self._profile_dir, name)
            )
            cell = ctk.CTkFrame(self._grid_host, corner_radius=6)
            cell.grid(row=i // cols, column=i % cols, padx=6, pady=6, sticky="n")

            if path:
                photo = _thumb_photo(path)
                if photo:
                    self._photos.append(photo)
                    lbl = tk.Label(cell, image=photo, bg="#2a2a2a", cursor="hand2")
                    lbl.pack(padx=4, pady=(4, 0))
                    lbl.bind(
                        "<Button-1>",
                        lambda _e, n=name: show_anchor_fullsize(
                            self.winfo_toplevel(),
                            None if self._shared_mode else self._profile_dir,
                            n,
                        ),
                    )

            title = name + (" ·使用中" if name in in_use else "")
            ctk.CTkLabel(cell, text=title, font=ctk.CTkFont(size=11), wraplength=100).pack(
                padx=2, pady=2
            )

            btn_row = ctk.CTkFrame(cell, fg_color="transparent")
            btn_row.pack(padx=2, pady=(0, 4))
            if self._editable:
                ctk.CTkButton(
                    btn_row,
                    text="刪除",
                    width=52,
                    height=22,
                    fg_color="#8b3a3a",
                    command=lambda n=name: self._delete(n),
                ).pack(side="left", padx=2)
            else:
                ctk.CTkLabel(btn_row, text="範例唯讀", text_color="#888", font=ctk.CTkFont(size=10)).pack()

    def _delete(self, name: str) -> None:
        if not self._editable:
            return
        if not self._shared_mode and self._profile_dir is None:
            return
        in_use: set[str] = set()
        if not self._shared_mode and self._profile and self._navigation:
            in_use = anchors_referenced_by_flow(self._profile, self._navigation)
        if name in in_use:
            from tkinter import messagebox

            if not messagebox.askyesno(
                "刪除圖示",
                f"「{name}」仍被流程或好友助戰步驟引用。\n仍要刪除檔案嗎？",
                parent=self.winfo_toplevel(),
            ):
                return
        try:
            delete_quest_anchor(
                name,
                profile_dir=self._profile_dir,
                shared=self._shared_mode,
            )
            if self._on_changed:
                self._on_changed()
            self._refresh()
        except Exception as exc:
            from tkinter import messagebox

            messagebox.showerror("刪除失敗", str(exc), parent=self.winfo_toplevel())
