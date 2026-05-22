from __future__ import annotations

import customtkinter as ctk

from fgo_auto.services.window_service import WindowCandidate, WindowService
from fgo_auto.ui.strings_zh import translate_message


class WindowPickerFrame(ctk.CTkFrame):
    def __init__(self, master, on_select, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self._on_select = on_select
        self._svc = WindowService()
        self._candidates: list[WindowCandidate] = []

        ctk.CTkLabel(self, text="視窗綁定", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=8, pady=(8, 4)
        )
        row = ctk.CTkFrame(self)
        row.pack(fill="x", padx=8, pady=4)
        self._rule_entry = ctk.CTkEntry(row, placeholder_text="視窗標題規則，例：BlueStacks")
        self._rule_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(row, text="重新整理", width=90, command=self.refresh).pack(side="right")

        self._list = ctk.CTkOptionMenu(self, values=["（請先按重新整理）"], command=self._picked)
        self._list.pack(fill="x", padx=8, pady=4)
        self._status = ctk.CTkLabel(self, text="", anchor="w")
        self._status.pack(fill="x", padx=8, pady=(0, 8))

    def set_rule(self, rule: str) -> None:
        self._rule_entry.delete(0, "end")
        self._rule_entry.insert(0, rule)

    def refresh(self) -> None:
        rule = self._rule_entry.get().strip()
        if not rule:
            self._status.configure(text="請輸入視窗標題規則")
            return
        try:
            self._candidates = self._svc.list_matching(rule)
        except Exception as exc:
            self._status.configure(text=translate_message(str(exc)))
            return
        if not self._candidates:
            self._status.configure(text=f"沒有符合的視窗：{rule!r}")
            self._list.configure(values=["（無符合視窗）"])
            return
        labels = [
            f"{w.handle} | {w.width}×{w.height} | {w.title[:60]}"
            for w in self._candidates
        ]
        self._list.configure(values=labels)
        self._list.set(labels[0])
        self._picked(labels[0])
        self._status.configure(text=f"找到 {len(self._candidates)} 個候選視窗")

    def _picked(self, label: str) -> None:
        if not self._candidates:
            return
        idx = 0
        values = self._list.cget("values")
        if label in values:
            idx = list(values).index(label)
        chosen = self._candidates[idx]
        self._on_select(chosen.handle, chosen.title)
