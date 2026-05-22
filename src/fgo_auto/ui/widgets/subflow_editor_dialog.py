from __future__ import annotations

from pathlib import Path
from typing import Callable

import customtkinter as ctk

from fgo_auto.quest.models import NavigationScript, NavigationStep
from fgo_auto.services.quest_flow_service import (
    FLOW_LABELS,
    STEP_KINDS_SUBFLOW,
    anchor_choices_for_profile,
    load_flow_script,
    save_flow_script,
)
from fgo_auto.ui.strings_zh import translate_message

# Reuse step row from flow_page would cause circular import — duplicate minimal host or import late


def open_subflow_editor(
    master,
    *,
    profile_dir: Path,
    flow_key: str,
    profile,
    editable: bool,
    on_saved: Callable[[], None] | None = None,
) -> None:
    """Edit steps for enter_quest / friend_support in a dialog."""
    from fgo_auto.ui.pages.flow_page import _StepRow  # noqa: PLC0415

    win = ctk.CTkToplevel(master)
    win.title(f"子流程：{FLOW_LABELS.get(flow_key, flow_key)}")
    win.geometry("920x420")
    win.transient(master)
    win.grab_set()

    script = load_flow_script(profile_dir, profile, flow_key)
    anchor_choices = anchor_choices_for_profile(profile_dir, script)
    if not anchor_choices:
        anchor_choices = ["（尚無圖示）"]

    ctk.CTkLabel(
        win,
        text=f"編輯「{FLOW_LABELS.get(flow_key, flow_key)}」的點擊步驟。主流程用「執行子流程」選擇此段。",
        wraplength=860,
        anchor="w",
    ).pack(fill="x", padx=12, pady=10)

    host = ctk.CTkScrollableFrame(win, height=240, label_text="步驟")
    host.pack(fill="both", expand=True, padx=12, pady=4)

    rows: list = []

    def rebuild(steps: list[NavigationStep]) -> None:
        for r in rows:
            r.destroy()
        rows.clear()
        for i, step in enumerate(steps):
            row = _StepRow(
                host,
                step,
                anchor_choices,
                profile_dir,
                on_delete=lambda idx=i: delete_step(idx),
                on_move=lambda delta, idx=i: move_step(idx, delta),
                step_kinds=STEP_KINDS_SUBFLOW,
            )
            row.pack(fill="x", pady=2)
            rows.append(row)

    def collect() -> list[NavigationStep]:
        return [r.to_step() for r in rows]

    def delete_step(index: int) -> None:
        steps = collect()
        if 0 <= index < len(steps):
            del steps[index]
            rebuild(steps)

    def move_step(index: int, delta: int) -> None:
        steps = collect()
        j = index + delta
        if 0 <= index < len(steps) and 0 <= j < len(steps):
            steps[index], steps[j] = steps[j], steps[index]
            rebuild(steps)

    rebuild(script.steps)

    add_row = ctk.CTkFrame(win)
    add_row.pack(fill="x", padx=12, pady=4)
    from fgo_auto.quest.models import DelayStep, TapAnchorStep

    ctk.CTkButton(
        add_row, text="＋點擊", width=72, command=lambda: rebuild(collect() + [TapAnchorStep(name="chaldea_gate")])
    ).pack(side="left", padx=2)
    ctk.CTkButton(
        add_row,
        text="＋等待",
        width=72,
        command=lambda: rebuild(collect() + [DelayStep(seconds=0.5)]),
    ).pack(side="left", padx=2)

    status = ctk.CTkLabel(win, text="", anchor="w", wraplength=860)
    status.pack(fill="x", padx=12, pady=4)

    def do_save() -> None:
        if not editable:
            status.configure(text="範例唯讀")
            return
        try:
            save_flow_script(profile_dir, flow_key, NavigationScript(steps=collect()))
            status.configure(text="已儲存")
            if on_saved:
                on_saved()
        except Exception as exc:
            status.configure(text=translate_message(str(exc)))

    btn_row = ctk.CTkFrame(win)
    btn_row.pack(fill="x", padx=12, pady=8)
    ctk.CTkButton(btn_row, text="儲存", command=do_save).pack(side="left", padx=4)
    ctk.CTkButton(btn_row, text="關閉", width=64, command=win.destroy).pack(side="right", padx=4)
