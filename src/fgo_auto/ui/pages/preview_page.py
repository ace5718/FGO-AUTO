from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Callable

import customtkinter as ctk
from PIL import Image, ImageTk

from fgo_auto.quest.loader import resolve_quest_profile_dir
from fgo_auto.services.quest_flow_service import anchor_choices_for_profile, save_quest_anchor_crop
from fgo_auto.ui.strings_zh import translate_message

_NEW_ANCHOR = "（新圖示名稱…）"


class PreviewPage(ctk.CTkFrame):
    """擷圖預覽；滑鼠拖曳框選後儲存為關卡圖示（錨點）。"""

    def __init__(
        self,
        master,
        on_capture: Callable[[], Path],
        get_quest_id: Callable[[], str | None] | None = None,
        on_anchor_saved: Callable[[], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_capture = on_capture
        self._get_quest_id = get_quest_id
        self._on_anchor_saved = on_anchor_saved
        self._full_size: tuple[int, int] = (0, 0)
        self._thumb_size: tuple[int, int] = (0, 0)
        self._selection_thumb: tuple[int, int, int, int] | None = None
        self._drag_start: tuple[int, int] | None = None
        self._tk_image: ImageTk.PhotoImage | None = None
        self._anchor_names: list[str] = []

        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=12, pady=12)
        ctk.CTkButton(top, text="擷圖", width=72, command=self._capture).pack(side="left", padx=(0, 8))

        self._quest_lbl = ctk.CTkLabel(top, text="關卡：—", width=200, anchor="w")
        self._quest_lbl.pack(side="left", padx=(0, 8))

        self._anchor_pick = ctk.CTkOptionMenu(top, values=[_NEW_ANCHOR], width=160, command=self._on_anchor_pick)
        self._anchor_pick.pack(side="left", padx=(0, 4))
        self._anchor_new = ctk.CTkEntry(top, width=120, placeholder_text="新名稱")
        self._anchor_new.pack(side="left", padx=(0, 8))
        self._anchor_new.pack_forget()

        ctk.CTkButton(top, text="儲存框選", width=88, command=self._save_selection).pack(side="left")

        ctk.CTkLabel(
            self,
            text="與「流程設定」同一關卡。先在那裡選本機關卡並「套用設定」，再來這裡擷圖存圖示。",
            anchor="w",
            wraplength=900,
            text_color="#aaaaaa",
        ).pack(fill="x", padx=12, pady=(0, 6))

        ctk.CTkLabel(
            self,
            text="① 擷圖　② 拖曳黃框　③ 選圖示名稱（或選「新圖示」輸入）　④ 儲存框選",
            anchor="w",
            wraplength=900,
        ).pack(fill="x", padx=12, pady=(0, 6))

        self._canvas_host = ctk.CTkFrame(self)
        self._canvas_host.pack(fill="both", expand=True, padx=12, pady=4)
        self._canvas = tk.Canvas(self._canvas_host, bg="#1a1a1a", highlightthickness=0, cursor="crosshair")
        self._canvas.pack()
        self._canvas.bind("<ButtonPress-1>", self._on_press)
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)

        self._status = ctk.CTkLabel(self, text="請先在「流程設定」選關卡並套用設定。", anchor="w", wraplength=900)
        self._status.pack(fill="x", padx=12, pady=(0, 12))

        self.refresh_quest()

    def refresh_quest(self) -> None:
        quest_id = self._get_quest_id() if self._get_quest_id else None
        if not quest_id:
            self._quest_lbl.configure(text="關卡：未選（請到流程設定）")
            self._anchor_names = []
            self._anchor_pick.configure(values=[_NEW_ANCHOR])
            self._anchor_pick.set(_NEW_ANCHOR)
            self._on_anchor_pick(_NEW_ANCHOR)
            return
        try:
            profile_dir = resolve_quest_profile_dir(quest_id)
            self._anchor_names = anchor_choices_for_profile(profile_dir, navigation=None)
            opts = [_NEW_ANCHOR, *self._anchor_names] if self._anchor_names else [_NEW_ANCHOR]
            self._anchor_pick.configure(values=opts)
            self._anchor_pick.set(opts[1] if len(opts) > 1 else _NEW_ANCHOR)
            self._on_anchor_pick(self._anchor_pick.get())
            self._quest_lbl.configure(text=f"關卡：{quest_id}")
        except Exception as exc:
            self._quest_lbl.configure(text=f"關卡：{quest_id}")
            self._status.configure(text=translate_message(str(exc)))

    def _on_anchor_pick(self, choice: str) -> None:
        if choice == _NEW_ANCHOR:
            self._anchor_new.pack(side="left", padx=(0, 8), after=self._anchor_pick)
        else:
            self._anchor_new.pack_forget()

    def _resolve_anchor_name(self) -> str:
        if self._anchor_pick.get() == _NEW_ANCHOR:
            return self._anchor_new.get().strip()
        return self._anchor_pick.get().strip()

    def _capture(self) -> None:
        try:
            path = self._on_capture()
            self.show_image(path)
            self._selection_thumb = None
            self._status.configure(text=f"已擷圖：{path.name}。請拖曳框選後儲存。")
        except Exception as exc:
            self._status.configure(text=translate_message(str(exc)))

    def show_image(self, path: Path) -> None:
        img = Image.open(path).convert("RGB")
        self._full_size = img.size
        thumb = img.copy()
        thumb.thumbnail((960, 540))
        self._thumb_size = thumb.size
        self._tk_image = ImageTk.PhotoImage(thumb)
        tw, th = self._thumb_size
        self._canvas.config(width=tw, height=th, scrollregion=(0, 0, tw, th))
        self._canvas.delete("all")
        self._canvas.create_image(0, 0, anchor="nw", image=self._tk_image)

    def _on_press(self, event: tk.Event) -> None:
        if self._tk_image is None:
            return
        self._drag_start = (event.x, event.y)
        self._canvas.delete("rubber")

    def _on_drag(self, event: tk.Event) -> None:
        if self._drag_start is None:
            return
        self._canvas.delete("rubber")
        x0, y0 = self._drag_start
        self._canvas.create_rectangle(
            x0, y0, event.x, event.y, outline="#ffcc00", width=2, tags="rubber"
        )

    def _on_release(self, event: tk.Event) -> None:
        if self._drag_start is None or self._thumb_size == (0, 0):
            return
        x0, y0 = self._drag_start
        x1, y1 = event.x, event.y
        self._drag_start = None
        left, right = sorted((x0, x1))
        top, bottom = sorted((y0, y1))
        tw, th = self._thumb_size
        if right - left < 6 or bottom - top < 6:
            self._selection_thumb = None
            self._status.configure(text="框太小，請重新拖曳。")
            return
        self._selection_thumb = (
            max(0, left),
            max(0, top),
            min(tw, right),
            min(th, bottom),
        )
        self._status.configure(text="已框選，請選圖示名稱後按「儲存框選」。")

    def _thumb_rect_to_full(self) -> tuple[int, int, int, int]:
        if self._selection_thumb is None:
            raise ValueError("no selection")
        x1, y1, x2, y2 = self._selection_thumb
        tw, th = self._thumb_size
        fw, fh = self._full_size
        if tw <= 0 or th <= 0:
            raise ValueError("bad thumb size")
        sx, sy = fw / tw, fh / th
        return (
            int(x1 * sx),
            int(y1 * sy),
            int(x2 * sx),
            int(y2 * sy),
        )

    def _save_selection(self) -> None:
        name = self._resolve_anchor_name()
        if not name:
            self._status.configure(text="請選擇或輸入圖示名稱。")
            return
        if self._selection_thumb is None:
            self._status.configure(text="請先在圖上用滑鼠拖曳框選區域。")
            return
        quest_id = self._get_quest_id() if self._get_quest_id else None
        if not quest_id:
            self._status.configure(text="請先到「流程設定」選本機關卡並按「套用設定」。")
            return
        try:
            rect = self._thumb_rect_to_full()
            path = save_quest_anchor_crop(quest_id, name, rect)
            self._status.configure(text=f"已存圖示：{path}（流程設定可選此名稱）")
            self.refresh_quest()
            if self._on_anchor_saved:
                self._on_anchor_saved()
        except Exception as exc:
            self._status.configure(text=translate_message(str(exc)))
