from __future__ import annotations

from pathlib import Path
from typing import Callable

import customtkinter as ctk

from fgo_auto.quest.models import NavigationStep
from fgo_auto.services.quest_flow_service import STEP_KINDS_MAIN, anchor_choices_for_profile
from fgo_auto.ui.strings_zh import translate_message


def open_nested_steps_editor(
    master,
    *,
    title: str,
    steps: list[NavigationStep],
    profile_dir: Path,
    step_kinds: dict[str, str] | None = None,
    subflow_choices: tuple[str, ...] = (),
    shared_anchor_resolution: str = "全部",
    on_pick_coordinate: Callable[[], tuple[int, int] | None] | None = None,
) -> list[NavigationStep] | None:
    """Modal editor for nested steps (if/else branches, for-loop body). Returns None if cancelled."""
    from fgo_auto.ui.pages.flow_page import _StepRow  # noqa: PLC0415

    result: list[list[NavigationStep] | None] = [None]

    win = ctk.CTkToplevel(master)
    win.title(title)
    win.geometry("920x440")
    win.transient(master)
    win.grab_set()

    ctk.CTkLabel(win, text=title, wraplength=860, anchor="w").pack(fill="x", padx=12, pady=10)

    host = ctk.CTkScrollableFrame(win, height=260, label_text="步驟")
    host.pack(fill="both", expand=True, padx=12, pady=4)

    kinds = step_kinds or STEP_KINDS_MAIN
    anchor_choices = anchor_choices_for_profile(profile_dir, None, resolution=shared_anchor_resolution)
    if not anchor_choices:
        anchor_choices = ["（尚無圖示）"]

    rows: list[_StepRow] = []

    def rebuild(current: list[NavigationStep]) -> None:
        for row in rows:
            row.destroy()
        rows.clear()
        for index, step in enumerate(current):
            row = _StepRow(
                host,
                step,
                anchor_choices,
                profile_dir,
                on_delete=lambda idx=index: delete_step(idx),
                on_move=lambda delta, idx=index: move_step(idx, delta),
                step_kinds=kinds,
                subflow_choices=subflow_choices,
                shared_anchor_resolution=shared_anchor_resolution,
                on_pick_coordinate=on_pick_coordinate,
            )
            row.pack(fill="x", pady=2)
            rows.append(row)

    def collect() -> list[NavigationStep]:
        return [row.to_step() for row in rows]

    def delete_step(index: int) -> None:
        current = collect()
        if 0 <= index < len(current):
            del current[index]
            rebuild(current)

    def move_step(index: int, delta: int) -> None:
        current = collect()
        new_index = index + delta
        if 0 <= index < len(current) and 0 <= new_index < len(current):
            current[index], current[new_index] = current[new_index], current[index]
            rebuild(current)

    rebuild(list(steps))

    add_row = ctk.CTkFrame(win)
    add_row.pack(fill="x", padx=12, pady=4)
    from fgo_auto.quest.models import DelayStep, ForRepeatStep, IfAnchorStep, TapAnchorStep

    ctk.CTkButton(
        add_row,
        text="＋點擊目標",
        width=88,
        command=lambda: rebuild(collect() + [TapAnchorStep(name="chaldea_gate")]),
    ).pack(side="left", padx=2)
    ctk.CTkButton(
        add_row,
        text="＋等待",
        width=72,
        command=lambda: rebuild(collect() + [DelayStep(seconds=0.5)]),
    ).pack(side="left", padx=2)
    ctk.CTkButton(
        add_row,
        text="＋條件",
        width=72,
        command=lambda: rebuild(collect() + [IfAnchorStep(name="chaldea_gate")]),
    ).pack(side="left", padx=2)
    ctk.CTkButton(
        add_row,
        text="＋重複",
        width=72,
        command=lambda: rebuild(collect() + [ForRepeatStep(count=2)]),
    ).pack(side="left", padx=2)

    status = ctk.CTkLabel(win, text="", anchor="w", wraplength=860)
    status.pack(fill="x", padx=12, pady=4)

    btn_row = ctk.CTkFrame(win)
    btn_row.pack(fill="x", padx=12, pady=8)

    def confirm() -> None:
        try:
            result[0] = collect()
            win.grab_release()
            win.destroy()
        except Exception as exc:
            status.configure(text=translate_message(str(exc)))

    def cancel() -> None:
        result[0] = None
        win.grab_release()
        win.destroy()

    ctk.CTkButton(btn_row, text="確定", width=72, command=confirm).pack(side="left", padx=4)
    ctk.CTkButton(btn_row, text="取消", width=72, fg_color="#555555", command=cancel).pack(side="left")

    win.wait_window()
    return result[0]
