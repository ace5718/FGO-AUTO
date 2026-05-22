from __future__ import annotations

import customtkinter as ctk

from fgo_auto.run_config import RunConfig


class SettingsPage(ctk.CTkScrollableFrame):
    def __init__(self, master, on_save, on_validate, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self._on_save = on_save
        self._on_validate = on_validate
        self._fields: dict[str, ctk.CTkEntry] = {}

        ctk.CTkLabel(self, text="Run 設定", font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=12, pady=(12, 8)
        )
        for key, label in (
            ("script", "Script"),
            ("loop_limit", "Loop limit"),
            ("window_title_rule", "Window title rule"),
            ("recognition_retries", "Recognition retries"),
            ("script_config", "Script config 路徑"),
        ):
            row = ctk.CTkFrame(self)
            row.pack(fill="x", padx=12, pady=4)
            ctk.CTkLabel(row, text=label, width=160, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(row)
            entry.pack(side="left", fill="x", expand=True)
            self._fields[key] = entry

        row = ctk.CTkFrame(self)
        row.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(row, text="Display preset", width=160, anchor="w").pack(side="left")
        self._display = ctk.CTkEntry(row)
        self._display.pack(side="left", fill="x", expand=True)

        btn_row = ctk.CTkFrame(self)
        btn_row.pack(fill="x", padx=12, pady=12)
        ctk.CTkButton(btn_row, text="驗證", command=self._validate).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="儲存至本機", command=self._save).pack(side="left")

        self._msg = ctk.CTkLabel(self, text="", anchor="w")
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
        )

    def _save(self) -> None:
        try:
            self._on_save(self._collect())
            self._msg.configure(text="已儲存至本機 profile")
        except Exception as exc:
            self._msg.configure(text=f"儲存失敗：{exc}")

    def _validate(self) -> None:
        try:
            summary = self._on_validate(self._collect())
            self._msg.configure(text=str(summary))
        except Exception as exc:
            self._msg.configure(text=f"驗證失敗：{exc}")
