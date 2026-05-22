from __future__ import annotations

from pathlib import Path
from typing import Callable

import customtkinter as ctk

from fgo_auto.quest.models import QuestProfile
from fgo_auto.services.quest_flow_service import (
    FRIEND_SUPPORT_FLOW_ZH,
    anchor_png_path,
    default_friend_support_config,
    ensure_friend_support_profile,
    friend_support_anchor_names,
    friend_support_anchor_plain,
    save_friend_support_settings,
)
from fgo_auto.ui.strings_zh import translate_message


class FriendSupportSettingsPanel(ctk.CTkFrame):
    """GUI for friend support: no manual profile.yaml editing."""

    def __init__(
        self,
        master,
        *,
        on_go_preview: Callable[[], None] | None = None,
        on_saved: Callable[[], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_go_preview = on_go_preview
        self._on_saved = on_saved
        self._profile_dir: Path | None = None
        self._profile: QuestProfile | None = None
        self._editable = False

        ctk.CTkLabel(
            self,
            text="好友助戰",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=8, pady=(8, 2))
        ctk.CTkLabel(
            self,
            text=FRIEND_SUPPORT_FLOW_ZH,
            anchor="w",
            wraplength=860,
            justify="left",
            text_color="#cccccc",
        ).pack(fill="x", padx=8, pady=(0, 6))

        cfg_row = ctk.CTkFrame(self)
        cfg_row.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(cfg_row, text="找不到好友時，最多按幾次「更新」", anchor="w").pack(side="left", padx=(0, 8))
        self._max_refresh = ctk.CTkEntry(cfg_row, width=48)
        self._max_refresh.insert(0, "20")
        self._max_refresh.pack(side="left", padx=(0, 8))
        self._save_btn = ctk.CTkButton(cfg_row, text="儲存好友設定", width=110, command=self._save)
        self._save_btn.pack(side="left", padx=(0, 8))
        self._enable_btn = ctk.CTkButton(
            cfg_row,
            text="啟用預設好友流程",
            width=130,
            fg_color="#1f538d",
            command=self._enable_default,
        )

        self._check_host = ctk.CTkFrame(self)
        self._check_host.pack(fill="x", padx=8, pady=6)
        self._check_labels: list[ctk.CTkLabel] = []

        self._hint = ctk.CTkLabel(
            self,
            text="",
            anchor="w",
            wraplength=860,
            text_color="#aaaaaa",
        )
        self._hint.pack(fill="x", padx=8, pady=(0, 8))

    def load(
        self,
        profile_dir: Path | None,
        profile: QuestProfile | None,
        *,
        editable: bool,
    ) -> None:
        self._profile_dir = profile_dir
        self._profile = profile
        self._editable = editable
        self._rebuild_checks()
        enabled = bool(profile and profile.friend_support and profile.friend_support.steps)
        if enabled and profile and profile.friend_support:
            self._max_refresh.delete(0, "end")
            self._max_refresh.insert(0, str(profile.friend_support.max_refresh_attempts))
            self._enable_btn.pack_forget()
            self._save_btn.pack(side="left", padx=(0, 8))
            self._hint.configure(
                text="已啟用。請在「預覽」依下方名稱各存一張小圖；編隊請在「流程設定」加步驟。"
            )
        else:
            self._save_btn.pack_forget()
            self._enable_btn.pack(side="left", padx=(0, 8))
            self._hint.configure(
                text="尚未啟用。請按「啟用預設好友流程」，再到「預覽」存三張圖。"
            )
        state = "normal" if editable else "disabled"
        self._max_refresh.configure(state=state)
        self._save_btn.configure(state=state)
        self._enable_btn.configure(state=state)

    def _rebuild_checks(self) -> None:
        for child in self._check_host.winfo_children():
            child.destroy()
        self._check_labels.clear()
        if self._profile_dir is None or self._profile is None:
            return
        names = friend_support_anchor_names(self._profile)
        for i, name in enumerate(names, 1):
            row = ctk.CTkFrame(self._check_host)
            row.pack(fill="x", pady=2)
            path = anchor_png_path(self._profile_dir, name)
            mark = "✓" if path else "✗"
            color = "#6fcf6f" if path else "#e07070"
            ctk.CTkLabel(row, text=mark, width=24, text_color=color).pack(side="left")
            plain = friend_support_anchor_plain(name)
            ctk.CTkLabel(row, text=f"{i}. {plain}", anchor="w").pack(side="left", fill="x", expand=True)
            if self._on_go_preview:
                ctk.CTkButton(
                    row,
                    text="去預覽存圖",
                    width=88,
                    height=24,
                    command=lambda n=name: self._go_preview_named(n),
                ).pack(side="right", padx=4)

    def _go_preview_named(self, _name: str) -> None:
        if self._on_go_preview:
            self._on_go_preview()

    def _parse_max_refresh(self) -> int:
        raw = self._max_refresh.get().strip()
        value = int(raw)
        if value < 1 or value > 60:
            raise ValueError("次數請填 1～60")
        return value

    def _enable_default(self) -> None:
        if not self._editable or self._profile_dir is None or self._profile is None:
            self._hint.configure(text="範例關卡無法改，請先「從範例複製」到本機")
            return
        try:
            max_refresh = self._parse_max_refresh()
            self._profile = ensure_friend_support_profile(
                self._profile_dir,
                self._profile,
                max_refresh_attempts=max_refresh,
            )
            self.load(self._profile_dir, self._profile, editable=True)
            if self._on_saved:
                self._on_saved()
            self._hint.configure(text="已啟用預設流程並儲存。")
        except Exception as exc:
            self._hint.configure(text=translate_message(str(exc)))

    def _save(self) -> None:
        if not self._editable or self._profile_dir is None or self._profile is None:
            return
        try:
            max_refresh = self._parse_max_refresh()
            self._profile = save_friend_support_settings(
                self._profile_dir,
                self._profile,
                max_refresh_attempts=max_refresh,
            )
            self._rebuild_checks()
            if self._on_saved:
                self._on_saved()
            self._hint.configure(text=f"已儲存（更新最多 {max_refresh} 次）。")
        except Exception as exc:
            self._hint.configure(text=translate_message(str(exc)))
