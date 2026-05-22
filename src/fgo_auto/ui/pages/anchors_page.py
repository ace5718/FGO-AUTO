from __future__ import annotations

from pathlib import Path
from typing import Callable

import customtkinter as ctk

from fgo_auto.services.quest_flow_service import (
    QuestProfileEntry,
    list_quest_profiles,
    list_shared_anchors,
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
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_go_preview = on_go_preview

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
        if on_go_preview:
            ctk.CTkButton(top, text="前往預覽存圖", width=100, command=on_go_preview).pack(side="left", padx=4)

        self._manager = AnchorManagerPanel(
            self,
            on_changed=self.reload,
            shared_mode=True,
        )
        self._manager.pack(fill="both", expand=True, padx=12, pady=4)

        self._status = ctk.CTkLabel(self, text="", anchor="w", wraplength=900)
        self._status.pack(fill="x", padx=12, pady=6)

        self.reload()

    def reload(self) -> None:
        root = shared_anchors_dir()
        self._status.configure(text=f"目錄：{root}　共 {len(list_shared_anchors())} 張圖")
        self._manager.load_shared(editable=True)

    def select_quest(self, quest_id: str) -> None:
        """Kept for app sync; shared library does not switch per quest."""
        self.reload()
