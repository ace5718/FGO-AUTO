from __future__ import annotations

import customtkinter as ctk

from fgo_auto.run.run_config import RunConfig
from fgo_auto.ui.strings_zh import translate_message


class SettingsPage(ctk.CTkScrollableFrame):
    def __init__(self, master, on_save, on_validate, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self._on_save = on_save
        self._on_validate = on_validate
        self._fields: dict[str, ctk.CTkEntry] = {}

        ctk.CTkLabel(self, text="Run 設定", font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=12, pady=(12, 8)
        )
        ctk.CTkLabel(
            self,
            text="顯示預設須與 BlueStacks「遊戲畫面」客戶區像素一致（不含標題列／外框，見 ADR-0005）。"
            "v2 方案請在「流程設定」或「執行」分頁套用，勿在此手填 ID。",
            anchor="w",
            wraplength=880,
        ).pack(fill="x", padx=12, pady=(0, 8))

        for key, label in (
            ("script", "腳本名稱"),
            ("loop_limit", "循環上限"),
            ("window_title_rule", "視窗標題規則"),
            ("recognition_retries", "辨識重試次數"),
            ("script_config", "腳本設定檔路徑"),
        ):
            row = ctk.CTkFrame(self)
            row.pack(fill="x", padx=12, pady=4)
            ctk.CTkLabel(row, text=label, width=160, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(row)
            entry.pack(side="left", fill="x", expand=True)
            self._fields[key] = entry

        row = ctk.CTkFrame(self)
        row.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(row, text="顯示預設（寬, 高）", width=160, anchor="w").pack(side="left")
        self._display = ctk.CTkEntry(row, placeholder_text="1920, 1080")
        self._display.pack(side="left", fill="x", expand=True)

        self._quest_profile: str | None = None
        self._loaded_script_version: str = "v0"

        btn_row = ctk.CTkFrame(self)
        btn_row.pack(fill="x", padx=12, pady=12)
        ctk.CTkButton(btn_row, text="驗證", command=self._validate).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="儲存至本機", command=self._save).pack(side="left")

        self._msg = ctk.CTkLabel(self, text="", anchor="w", wraplength=880)
        self._msg.pack(fill="x", padx=12, pady=8)

    def load_config(self, config: RunConfig) -> None:
        data = config.model_dump()
        for key, entry in self._fields.items():
            entry.delete(0, "end")
            val = data.get(key)
            if val is not None:
                entry.insert(0, str(val))
        self._display.delete(0, "end")
        self._display.insert(0, f"{config.display_preset[0]}, {config.display_preset[1]}")
        self._loaded_script_version = config.script_version
        self._quest_profile = config.quest_profile

    def _collect(self) -> RunConfig:
        preset_parts = [p.strip() for p in self._display.get().split(",")]
        preset = (int(preset_parts[0]), int(preset_parts[1]))
        return RunConfig(
            script=self._fields["script"].get().strip(),
            loop_limit=int(self._fields["loop_limit"].get()),
            window_title_rule=self._fields["window_title_rule"].get().strip(),
            recognition_retries=int(self._fields["recognition_retries"].get()),
            display_preset=preset,
            script_config=self._fields["script_config"].get().strip() or None,
            script_version=self._loaded_script_version,
            quest_profile=self._quest_profile,
        )

    def _save(self) -> None:
        try:
            cfg = self._collect()
            if cfg.script_version == "v2" and not cfg.quest_profile:
                self._msg.configure(
                    text="v2 請先在「執行」分頁選擇並套用方案。"
                )
                return
            self._on_save(cfg)
            self._msg.configure(text="已儲存至 data/profiles/default/run.yaml")
        except Exception as exc:
            self._msg.configure(text=f"儲存失敗：{translate_message(str(exc))}")

    def _validate(self) -> None:
        try:
            summary = self._on_validate(self._collect())
            self._msg.configure(text=str(summary))
        except Exception as exc:
            self._msg.configure(text=f"驗證失敗：{translate_message(str(exc))}")
