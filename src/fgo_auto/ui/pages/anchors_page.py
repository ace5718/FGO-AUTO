from __future__ import annotations

from pathlib import Path
from typing import Callable

import customtkinter as ctk

from fgo_auto.services.quest_flow_service import (
    QuestProfileEntry,
    list_quest_profiles,
    list_shared_anchors,
    shared_anchor_resolutions,
    shared_anchors_dir,
)
from fgo_auto.ui.strings_zh import translate_message
from fgo_auto.ui.widgets.anchor_manager_panel import AnchorManagerPanel


class AnchorsPage(ctk.CTkFrame):
    """Shared anchor library under data/anchors/ (used by all quests)."""

    def __init__(
        self,
        master,
        on_go_preview: Callable[[], None] | None = None,
        on_resolution_change: Callable[[str], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_go_preview = on_go_preview
        self._on_resolution_change = on_resolution_change
        self._selected_resolution = "全部"

        ctk.CTkLabel(
            self,
            text="共用圖示庫",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(12, 4))
        ctk.CTkLabel(
            self,
            text="多數按鈕圖示（職階、更新、迦勒底之門等）只需存一份，所有關卡共用。"
            "少數關卡專用圖示請在「預覽」選「存到本關卡」。",
            anchor="w",
            wraplength=900,
        ).pack(fill="x", padx=12, pady=(0, 8))

        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=12, pady=6)
        ctk.CTkButton(top, text="重新整理", width=80, command=self.reload).pack(side="left", padx=4)
        self._resolution_menu = ctk.CTkOptionMenu(
            top,
            values=["全部"],
            width=120,
            command=self._on_resolution_change_menu,
        )
        self._resolution_menu.pack(side="left", padx=4)

        self._manager = AnchorManagerPanel(
            self,
            on_changed=self.reload,
            shared_mode=True,
        )
        self._manager.pack(fill="both", expand=True, padx=12, pady=4)

        self._status = ctk.CTkLabel(self, text="", anchor="w", wraplength=900)
        self._status.pack(fill="x", padx=12, pady=6)

        self.reload()

    def set_resolution(self, resolution: str) -> None:
        self._selected_resolution = resolution
        self.reload()

    def _on_resolution_change_menu(self, selected: str) -> None:
        self._selected_resolution = selected
        if self._on_resolution_change:
            self._on_resolution_change(selected)
        self._status.configure(
            text=f"目錄：{shared_anchors_dir()}　解析度：{selected}　共 {len(list_shared_anchors(selected))} 張圖"
        )
        self._manager.load_shared(editable=True, resolution=selected)

    def reload(self) -> None:
        root = shared_anchors_dir()
        resolutions = ["全部", *shared_anchor_resolutions()]
        self._resolution_menu.configure(values=resolutions)
        self._resolution_menu.set(self._selected_resolution if self._selected_resolution in resolutions else "全部")
        selected = self._resolution_menu.get()
        self._selected_resolution = selected
        anchors = list_shared_anchors(selected)
        self._status.configure(
            text=f"目錄：{root}　解析度：{selected}　共 {len(anchors)} 張圖"
        )
        self._manager.load_shared(editable=True, resolution=selected)

    def select_quest(self, quest_id: str) -> None:
        """Kept for app sync; shared library does not switch per quest."""
        self.reload()
