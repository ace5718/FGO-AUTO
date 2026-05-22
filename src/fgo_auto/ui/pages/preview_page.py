from __future__ import annotations

from pathlib import Path

import customtkinter as ctk
from PIL import Image

from fgo_auto.services.config_service import ConfigService


class PreviewPage(ctk.CTkFrame):
    """擷圖預覽；Phase 2 框選占位。"""

    def __init__(self, master, on_capture, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self._on_capture = on_capture
        self._photo: ctk.CTkImage | None = None

        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=12, pady=12)
        ctk.CTkButton(top, text="擷圖", command=self._capture).pack(side="left", padx=(0, 8))
        self._phase2_btn = ctk.CTkButton(
            top,
            text="框選 Anchor（Phase 2）",
            state="disabled",
            command=self._phase2_crop,
        )
        self._phase2_btn.pack(side="left")

        self._preview = ctk.CTkLabel(self, text="尚無預覽")
        self._preview.pack(fill="both", expand=True, padx=12, pady=8)
        self._status = ctk.CTkLabel(self, text="", anchor="w")
        self._status.pack(fill="x", padx=12, pady=(0, 12))

    def _capture(self) -> None:
        try:
            path = self._on_capture()
            self.show_image(path)
            self._status.configure(text=f"已儲存：{path}")
        except Exception as exc:
            self._status.configure(text=str(exc))

    def show_image(self, path: Path) -> None:
        img = Image.open(path)
        img.thumbnail((960, 540))
        self._photo = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
        self._preview.configure(image=self._photo, text="")

    def _phase2_crop(self) -> None:
        svc = ConfigService()
        try:
            svc.save_anchor_crop("preview", (0, 0, 0, 0))
        except NotImplementedError:
            self._status.configure(text="Phase 2：預覽框選 Anchor 尚未實作（見 issue #10）")
