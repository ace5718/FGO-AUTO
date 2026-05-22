from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from fgo_auto.run.controller import RunOutcome
from fgo_auto.ui.strings_zh import outcome_label, screen_state_label, translate_message


class RunPage(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_start,
        on_stop,
        on_apply_run_quest: Callable[[str], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_start = on_start
        self._on_stop = on_stop
        self._on_apply_run_quest = on_apply_run_quest
        self._quest_ids: list[str] = []

        ctk.CTkLabel(
            self,
            text="① 綁定視窗　② 選擇要執行的流程並套用　③「設定」儲存　④ 開始執行",
            anchor="w",
            wraplength=900,
            font=ctk.CTkFont(size=13),
        ).pack(fill="x", padx=12, pady=(8, 4))

        flow_row = ctk.CTkFrame(self)
        flow_row.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(flow_row, text="執行流程", width=72, anchor="w").pack(side="left")
        self._quest_menu = ctk.CTkOptionMenu(flow_row, values=["（請到流程設定建立）"], width=260, command=self._on_quest_menu)
        self._quest_menu.pack(side="left", padx=4)
        ctk.CTkButton(flow_row, text="套用此流程", width=88, command=self._apply_quest).pack(side="left", padx=4)
        self._flow_status = ctk.CTkLabel(flow_row, text="", anchor="w", text_color="#aaaaaa")
        self._flow_status.pack(side="left", padx=8)

        ctk.CTkLabel(self, text="執行控制", font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=12, pady=(12, 8)
        )
        row = ctk.CTkFrame(self)
        row.pack(fill="x", padx=12, pady=8)
        ctk.CTkButton(row, text="開始執行", command=self._start).pack(side="left", padx=(0, 8))
        ctk.CTkButton(row, text="手動停止", fg_color="#8b3a3a", command=self._on_stop).pack(
            side="left"
        )

        self._state_lbl = ctk.CTkLabel(self, text="畫面狀態：—", anchor="w")
        self._state_lbl.pack(fill="x", padx=12, pady=4)
        self._loops_lbl = ctk.CTkLabel(self, text="已完成循環：0", anchor="w")
        self._loops_lbl.pack(fill="x", padx=12, pady=4)
        self._outcome_lbl = ctk.CTkLabel(self, text="執行結果：—", anchor="w")
        self._outcome_lbl.pack(fill="x", padx=12, pady=4)
        self._hint = ctk.CTkLabel(self, text="", anchor="w", wraplength=700)
        self._hint.pack(fill="x", padx=12, pady=12)

    def set_quest_choices(self, items: list[tuple[str, str]], active_id: str | None = None) -> None:
        """items: (quest_id, menu label)."""
        self._quest_ids = [q for q, _ in items]
        labels = [label for _, label in items] or ["（無）"]
        self._quest_menu.configure(values=labels)
        if active_id and active_id in self._quest_ids:
            idx = self._quest_ids.index(active_id)
            self._quest_menu.set(labels[idx])
        elif labels:
            self._quest_menu.set(labels[0])

    def show_active_flow(self, quest_id: str | None, script_version: str) -> None:
        if quest_id:
            self._flow_status.configure(text=f"目前設定：v{script_version} · {quest_id}")
        else:
            self._flow_status.configure(text=f"目前設定：v{script_version} · 未選關卡")

    def _on_quest_menu(self, _label: str) -> None:
        pass

    def selected_quest_id(self) -> str | None:
        if not self._quest_ids:
            return None
        label = self._quest_menu.get()
        labels = list(self._quest_menu.cget("values"))
        if label not in labels:
            return None
        return self._quest_ids[labels.index(label)]

    def _apply_quest(self) -> None:
        quest_id = self.selected_quest_id()
        if not quest_id or self._on_apply_run_quest is None:
            self._hint.configure(text="請先選擇流程")
            return
        self._on_apply_run_quest(quest_id)

    def _start(self) -> None:
        msg = self._on_start()
        if msg:
            self._hint.configure(text=translate_message(msg))

    def update_status(
        self,
        *,
        screen_state: str = "",
        loops: int | None = None,
        outcome: RunOutcome | None = None,
        message: str = "",
    ) -> None:
        if screen_state:
            self._state_lbl.configure(
                text=f"畫面狀態：{screen_state_label(screen_state)}（{screen_state}）"
            )
        if loops is not None:
            self._loops_lbl.configure(text=f"已完成循環：{loops}")
        if outcome is not None:
            self._outcome_lbl.configure(text=f"執行結果：{outcome_label(outcome)}")
        if message:
            self._hint.configure(text=translate_message(message))
