from __future__ import annotations

import customtkinter as ctk


class LogsPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self._text = ctk.CTkTextbox(self)
        self._text.pack(fill="both", expand=True, padx=12, pady=12)
        ctk.CTkLabel(
            self,
            text="日誌僅顯示自動執行流程的狀態與結果；系統內部錯誤不會直接寫入此處。",
            anchor="w",
            wraplength=900,
        ).pack(fill="x", padx=12, pady=(0, 8))

    def append_line(self, line: str) -> None:
        self._text.insert("end", line + "\n")
        self._text.see("end")
