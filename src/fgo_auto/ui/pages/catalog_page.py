from __future__ import annotations

import customtkinter as ctk

from fgo_auto.services.config_service import ConfigService


class CatalogPage(ctk.CTkScrollableFrame):
    """Phase 2：Screen state 模板管理占位。"""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, **kwargs)
        ctk.CTkLabel(
            self,
            text="Catalog 管理（Phase 2）",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=12, pady=12)
        ctk.CTkLabel(
            self,
            text="上傳／預覽／刪除 State catalog 模板將於 Phase 2 提供。",
            anchor="w",
        ).pack(fill="x", padx=12, pady=4)
        ctk.CTkButton(self, text="列出 Screen state", command=self._list_states).pack(
            anchor="w", padx=12, pady=8
        )
        self._output = ctk.CTkTextbox(self, height=200)
        self._output.pack(fill="both", expand=True, padx=12, pady=8)

    def _list_states(self) -> None:
        svc = ConfigService()
        try:
            states = svc.list_catalog_states()
            text = "\n".join(states)
        except NotImplementedError as exc:
            text = str(exc)
        self._output.delete("1.0", "end")
        self._output.insert("1.0", text)
