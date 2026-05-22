from __future__ import annotations

import customtkinter as ctk

from fgo_auto.services.config_service import ConfigService


class CatalogPage(ctk.CTkScrollableFrame):
    """Phase 2：畫面狀態模板管理占位。"""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, **kwargs)
        ctk.CTkLabel(
            self,
            text="模板庫管理（Phase 2）",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=12, pady=12)
        ctk.CTkLabel(
            self,
            text="之後可在此上傳／預覽／刪除各畫面狀態（Screen state）的辨識模板 PNG。",
            anchor="w",
            wraplength=880,
        ).pack(fill="x", padx=12, pady=4)
        ctk.CTkButton(self, text="列出畫面狀態", command=self._list_states).pack(
            anchor="w", padx=12, pady=8
        )
        self._output = ctk.CTkTextbox(self, height=200)
        self._output.pack(fill="both", expand=True, padx=12, pady=8)

    def _list_states(self) -> None:
        svc = ConfigService()
        try:
            cfg = svc.load_run()
            states = svc.list_catalog_states(cfg.display_preset)
            text = "\n".join(states) if states else "(尚無子目錄；請在 data/catalog/{w}x{h}/ 放置模板)"
        except Exception as exc:
            text = str(exc)
        self._output.delete("1.0", "end")
        self._output.insert("1.0", text)
