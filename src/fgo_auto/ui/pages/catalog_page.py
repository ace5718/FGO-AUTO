from __future__ import annotations

from pathlib import Path
from typing import Callable

import customtkinter as ctk

from fgo_auto.services.catalog_service import (
    catalog_preset_dir,
    count_templates,
    save_state_template,
)
from fgo_auto.services.config_service import ConfigService
from fgo_auto.services.paths import catalog_dir_for_preset
from fgo_auto.ui.strings_zh import translate_message


class CatalogPage(ctk.CTkScrollableFrame):
    """畫面狀態模板庫：須與 BlueStacks 視窗同解析度。"""

    def __init__(self, master, on_capture: Callable[[], Path] | None = None, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self._on_capture = on_capture

        ctk.CTkLabel(
            self,
            text="模板庫（Screen state）",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=12, pady=12)
        ctk.CTkLabel(
            self,
            text="辨識失敗多半是此處沒有「與遊戲同尺寸」的模板。請在遊戲主畫面按下方按鈕擷圖存檔。",
            anchor="w",
            wraplength=880,
        ).pack(fill="x", padx=12, pady=4)

        row = ctk.CTkFrame(self)
        row.pack(fill="x", padx=12, pady=8)
        ctk.CTkButton(row, text="擷圖→存為主畫面模板", command=self._save_main_template).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(row, text="重新整理", width=80, command=self._refresh).pack(side="left")

        self._info = ctk.CTkLabel(self, text="", anchor="w", wraplength=880)
        self._info.pack(fill="x", padx=12, pady=4)

        self._output = ctk.CTkTextbox(self, height=160)
        self._output.pack(fill="both", expand=True, padx=12, pady=8)

        self._refresh()

    def _refresh(self) -> None:
        try:
            cfg = ConfigService().load_run()
            preset = cfg.display_preset
            root = catalog_dir_for_preset(preset[0], preset[1])
            n = count_templates(preset)
            self._info.configure(
                text=f"顯示預設 {preset[0]}×{preset[1]}　模板數 {n}　目錄：{catalog_preset_dir(*preset)}"
            )
            states = [
                p.name
                for p in sorted(root.iterdir())
                if p.is_dir() and not p.name.startswith(".")
            ] if root.is_dir() else []
            lines = [f"使用目錄：{root}", f"子目錄：{', '.join(states) or '（無）'}"]
            for state in states:
                pngs = list((root / state).glob("*.png"))
                lines.append(f"  {state}/：{', '.join(p.name for p in pngs) or '（無 PNG）'}")
            self._output.delete("1.0", "end")
            self._output.insert("1.0", "\n".join(lines))
        except Exception as exc:
            self._info.configure(text=translate_message(str(exc)))

    def _save_main_template(self) -> None:
        if self._on_capture is None:
            self._info.configure(text="請先在「執行」綁定視窗")
            return
        try:
            path = self._on_capture()
            cfg = ConfigService().load_run()
            dest = save_state_template(cfg.display_preset, "main", path)
            self._info.configure(text=f"已儲存：{dest}　請停止執行後再「開始」以載入新模板")
            self._refresh()
        except Exception as exc:
            self._info.configure(text=translate_message(str(exc)))
