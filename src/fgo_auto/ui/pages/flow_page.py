from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Callable

import customtkinter as ctk
from PIL import Image, ImageTk

from fgo_auto.quest.models import (
    DelayStep,
    NavigationScript,
    NavigationStep,
    RunSubflowStep,
    ScrollUntilAnchorStep,
    TapAnchorStep,
    WaitScreenStep,
)
from fgo_auto.services.quest_flow_service import (
    FLOW_GUIDE,
    SCREEN_STATE_ZH,
    STEP_KIND_ZH,
    QuestProfileEntry,
    anchor_choices_for_profile,
    anchor_png_path,
    copy_profile_to_user,
    create_blank_profile,
    list_quest_profiles,
    load_flow,
    save_navigation,
)
from fgo_auto.ui.strings_zh import translate_message
from fgo_auto.ui.widgets.anchor_preview_dialog import show_anchor_fullsize

_NO_ANCHOR = "（尚無圖示，請到預覽新增）"
_DELAY_CHOICES = ("0.5", "1", "2", "3", "5")
_SCROLL_ATTEMPTS = ("5", "8", "10", "12", "15")
_SCREEN_CHOICES = tuple(SCREEN_STATE_ZH.keys())
_SUBFLOW_CHOICES = ("friend_support",)
_THUMB_SIZE = (100, 64)


def _pil_anchor_thumb(path: Path) -> Image.Image:
    """Load anchor PNG for display (RGBA flattened; same path as preview page)."""
    img = Image.open(path)
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (48, 48, 48))
        bg.paste(img, mask=img.split()[3])
        return bg
    return img.convert("RGB")


def _load_anchor_photo(profile_dir: Path | None, name: str) -> ImageTk.PhotoImage | None:
    if profile_dir is None:
        return None
    path = anchor_png_path(profile_dir, name)
    if path is None:
        return None
    try:
        img = _pil_anchor_thumb(path)
        img.thumbnail(_THUMB_SIZE, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except OSError:
        return None


class _StepRow(ctk.CTkFrame):
    """One flow step: kind + pickers + anchor thumbnail preview."""

    def __init__(
        self,
        master,
        step: NavigationStep,
        anchor_choices: list[str],
        profile_dir: Path | None,
        on_delete: Callable[[], None],
        on_move: Callable[[int], None],
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._anchor_choices = anchor_choices or [_NO_ANCHOR]
        self._profile_dir = profile_dir
        self._thumb_photo: ImageTk.PhotoImage | None = None

        kinds = list(STEP_KIND_ZH.keys())
        self._kind_menu = ctk.CTkOptionMenu(self, values=kinds, width=120, command=self._on_kind)
        self._kind_menu.pack(side="left", padx=4, pady=6)

        self._detail = ctk.CTkFrame(self)
        self._detail.pack(side="left", padx=4)
        self._pickers: dict[str, ctk.CTkOptionMenu] = {}

        self._thumb_box = ctk.CTkFrame(self, width=_THUMB_SIZE[0] + 4, height=_THUMB_SIZE[1] + 4)
        self._thumb_box.pack(side="left", padx=6, pady=4)
        self._thumb_box.pack_propagate(False)
        # 勿對 tk.Label 設 width/height（單位是字元數，會變成大片黑底）
        self._thumb_lbl = tk.Label(self._thumb_box, text="—", bg="#3a3a3a", fg="#aaaaaa", cursor="hand2")
        self._thumb_lbl.place(relx=0.5, rely=0.5, anchor="center")
        self._thumb_lbl.bind("<Button-1>", lambda _e: self._open_full_image())

        ctk.CTkButton(self, text="↑", width=28, command=lambda: on_move(-1)).pack(side="left", padx=2)
        ctk.CTkButton(self, text="↓", width=28, command=lambda: on_move(1)).pack(side="left", padx=2)
        ctk.CTkButton(self, text="刪", width=36, fg_color="#8b3a3a", command=on_delete).pack(
            side="right", padx=4
        )
        self._load_step(step)

    def _clear_detail(self) -> None:
        for child in self._detail.winfo_children():
            child.destroy()
        self._pickers.clear()

    def _show_thumb(self, name: str | None) -> None:
        if not name:
            self._thumb_photo = None
            self._thumb_lbl.configure(image="", text="—")
            return
        photo = _load_anchor_photo(self._profile_dir, name)
        if photo is None:
            self._thumb_photo = None
            self._thumb_lbl.configure(image="", text="無圖")
            return
        self._thumb_photo = photo
        self._thumb_lbl.configure(image=photo, text="")

    def _open_full_image(self) -> None:
        if self._kind_menu.get() not in ("點擊", "往下滑找圖示"):
            return
        name = self._pick("anchor") if "anchor" in self._pickers else None
        if name and not name.startswith("（"):
            show_anchor_fullsize(self.winfo_toplevel(), self._profile_dir, name)

    def _on_anchor_pick(self, name: str) -> None:
        self._show_thumb(name)

    def _add_picker(
        self,
        key: str,
        label: str,
        values: tuple[str, ...],
        width: int = 180,
        *,
        on_change: Callable[[str], None] | None = None,
    ) -> ctk.CTkOptionMenu:
        row = ctk.CTkFrame(self._detail)
        row.pack(fill="x", pady=1)
        ctk.CTkLabel(row, text=label, width=52, anchor="w").pack(side="left")
        menu = ctk.CTkOptionMenu(row, values=list(values), width=width, command=on_change)
        menu.pack(side="left")
        self._pickers[key] = menu
        return menu

    def _pick(self, key: str) -> str:
        return self._pickers[key].get().strip()

    def _set_pick(self, key: str, value: str, values: tuple[str, ...]) -> None:
        menu = self._pickers[key]
        opts = list(values)
        if value and value not in opts:
            opts = [value, *opts]
        menu.configure(values=opts)
        menu.set(value if value in opts else opts[0])

    def _load_step(self, step: NavigationStep) -> None:
        if isinstance(step, TapAnchorStep):
            self._kind_menu.set("點擊")
            self._on_kind("點擊")
            self._set_pick("anchor", step.name, tuple(self._anchor_choices))
            self._show_thumb(step.name)
        elif isinstance(step, ScrollUntilAnchorStep):
            self._kind_menu.set("往下滑找圖示")
            self._on_kind("往下滑找圖示")
            self._set_pick("anchor", step.name, tuple(self._anchor_choices))
            self._set_pick("attempts", str(step.max_attempts), _SCROLL_ATTEMPTS)
            self._show_thumb(step.name)
        elif isinstance(step, DelayStep):
            self._kind_menu.set("等待秒")
            self._on_kind("等待秒")
            sec = str(step.seconds)
            if sec not in _DELAY_CHOICES:
                self._set_pick("seconds", sec, (sec, *_DELAY_CHOICES))
            else:
                self._set_pick("seconds", sec, _DELAY_CHOICES)
        elif isinstance(step, WaitScreenStep):
            self._kind_menu.set("等待畫面")
            self._on_kind("等待畫面")
            zh = next((k for k, v in SCREEN_STATE_ZH.items() if v == step.state), "主畫面")
            self._set_pick("screen", zh, _SCREEN_CHOICES)
        elif isinstance(step, RunSubflowStep):
            self._kind_menu.set("好友助戰")
            self._on_kind("好友助戰")

    def _on_kind(self, kind: str) -> None:
        self._clear_detail()
        if kind in ("點擊", "往下滑找圖示"):
            self._add_picker(
                "anchor",
                "圖示",
                tuple(self._anchor_choices),
                on_change=self._on_anchor_pick,
            )
            self._on_anchor_pick(self._pickers["anchor"].get())
            if kind == "往下滑找圖示":
                self._add_picker("attempts", "次數", _SCROLL_ATTEMPTS, width=72)
        elif kind == "等待秒":
            self._show_thumb(None)
            self._add_picker("seconds", "秒數", _DELAY_CHOICES, width=72)
        elif kind == "等待畫面":
            self._show_thumb(None)
            self._add_picker("screen", "畫面", _SCREEN_CHOICES)
        elif kind == "好友助戰":
            self._show_thumb(None)
            self._add_picker("subflow", "流程", _SUBFLOW_CHOICES)

    def _resolve_anchor_name(self) -> str:
        name = self._pick("anchor")
        if not name or name.startswith("（"):
            raise ValueError("請從下拉選擇圖示，或先到預覽儲存圖示")
        return name

    def to_step(self) -> NavigationStep:
        kind = self._kind_menu.get()
        action = STEP_KIND_ZH[kind]
        if action == "tap_anchor":
            return TapAnchorStep(name=self._resolve_anchor_name())
        if action == "scroll_until_anchor":
            return ScrollUntilAnchorStep(
                name=self._resolve_anchor_name(),
                max_attempts=int(self._pick("attempts")),
            )
        if action == "delay":
            return DelayStep(seconds=float(self._pick("seconds")))
        if action == "wait_screen":
            return WaitScreenStep(state=SCREEN_STATE_ZH[self._pick("screen")], timeout_s=15.0)
        return RunSubflowStep(ref=self._pick("subflow"))


class FlowPage(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_apply_quest_profile: Callable[[str], None] | None = None,
        on_quest_selected: Callable[[str], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_apply_quest = on_apply_quest_profile
        self._on_quest_selected = on_quest_selected
        self._entries: list[QuestProfileEntry] = []
        self._profile_dir: Path | None = None
        self._anchor_choices: list[str] = [_NO_ANCHOR]
        self._step_rows: list[_StepRow] = []

        ctk.CTkLabel(self, text=FLOW_GUIDE, justify="left", wraplength=880).pack(
            anchor="w", padx=12, pady=(10, 4)
        )

        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(top, text="關卡", width=40).pack(side="left")
        self._profile_menu = ctk.CTkOptionMenu(top, values=["…"], width=280, command=self._on_profile_pick)
        self._profile_menu.pack(side="left", padx=4)
        ctk.CTkButton(top, text="儲存", width=56, command=self.save).pack(side="left", padx=4)
        ctk.CTkButton(top, text="套用設定", width=80, command=self._apply_to_run).pack(side="left")
        ctk.CTkButton(top, text="重新載入圖示", width=100, command=self.reload).pack(side="left", padx=4)

        copy_row = ctk.CTkFrame(self)
        copy_row.pack(fill="x", padx=12, pady=2)
        self._new_id = ctk.CTkEntry(copy_row, placeholder_text="新關卡 ID（英文底線）", width=160)
        self._new_id.pack(side="left", padx=(0, 6))
        self._new_name = ctk.CTkEntry(copy_row, placeholder_text="顯示名稱（可選）", width=120)
        self._new_name.pack(side="left", padx=(0, 6))
        ctk.CTkButton(copy_row, text="新增空白流程", width=100, command=self._create_blank).pack(side="left", padx=2)
        ctk.CTkButton(copy_row, text="從範例複製", width=90, command=self._copy_from_example).pack(side="left", padx=2)

        self._steps_host = ctk.CTkScrollableFrame(self, height=280, label_text="點擊順序（點右側縮圖可看全圖）")
        self._steps_host.pack(fill="both", expand=True, padx=12, pady=4)

        add_row = ctk.CTkFrame(self)
        add_row.pack(fill="x", padx=12, pady=4)
        ctk.CTkButton(add_row, text="＋點擊", width=72, command=self._add_tap).pack(side="left", padx=2)
        ctk.CTkButton(add_row, text="＋往下滑找", width=96, command=self._add_scroll).pack(side="left", padx=2)
        ctk.CTkButton(add_row, text="＋等待", width=72, command=lambda: self._add_step(DelayStep(seconds=0.5))).pack(
            side="left", padx=2
        )
        ctk.CTkButton(
            add_row, text="＋好友", width=72, command=lambda: self._add_step(RunSubflowStep(ref="friend_support"))
        ).pack(side="left", padx=2)

        self._status = ctk.CTkLabel(self, text="", anchor="w", wraplength=880)
        self._status.pack(fill="x", padx=12, pady=6)

        self.reload_profiles()

    def _default_anchor(self) -> str:
        if self._anchor_choices and self._anchor_choices[0] != _NO_ANCHOR:
            return self._anchor_choices[0]
        return "chaldea_gate"

    def _add_tap(self) -> None:
        self._add_step(TapAnchorStep(name=self._default_anchor()))

    def _add_scroll(self) -> None:
        self._add_step(ScrollUntilAnchorStep(name=self._default_anchor(), max_attempts=8))

    def reload_profiles(self) -> None:
        self._entries = list_quest_profiles()
        if not self._entries:
            self._profile_menu.configure(values=["（無）"])
            return
        labels = [f"{e.display_name or e.quest_id}" + (" ·本機" if e.is_user_copy else " ·範例") for e in self._entries]
        self._profile_menu.configure(values=labels)
        self._profile_menu.set(labels[0])
        self.reload()

    def _selected_entry(self) -> QuestProfileEntry | None:
        if not self._entries:
            return None
        label = self._profile_menu.get()
        idx = list(self._profile_menu.cget("values")).index(label)
        return self._entries[idx]

    def _on_profile_pick(self, _label: str) -> None:
        self.reload()

    def reload(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            return
        try:
            profile, navigation, profile_dir = load_flow(entry.quest_id)
            self._profile_dir = profile_dir
            self._anchor_choices = anchor_choices_for_profile(profile_dir, navigation)
            if not self._anchor_choices:
                self._anchor_choices = [_NO_ANCHOR]
            current = self._collect_steps() if self._step_rows else None
            self._set_steps(current if current is not None else navigation.steps)
            note = "可改" if entry.is_user_copy else "範例請先複製"
            self._status.configure(text=f"{entry.quest_id}（{note}）　圖示目錄：{profile_dir / 'anchors'}")
            if self._on_quest_selected:
                self._on_quest_selected(entry.quest_id)
        except Exception as exc:
            self._status.configure(text=translate_message(str(exc)))

    def _clear_steps(self) -> None:
        for row in self._step_rows:
            row.destroy()
        self._step_rows.clear()

    def _set_steps(self, steps: list[NavigationStep]) -> None:
        self._clear_steps()
        for step in steps:
            self._append_row(step)

    def _append_row(self, step: NavigationStep) -> None:
        idx = len(self._step_rows)
        row = _StepRow(
            self._steps_host,
            step,
            self._anchor_choices,
            self._profile_dir,
            on_delete=lambda r=idx: self._delete_step(r),
            on_move=lambda delta, r=idx: self._move_step(r, delta),
        )
        row.pack(fill="x", pady=2)
        self._step_rows.append(row)

    def _add_step(self, step: NavigationStep) -> None:
        self._append_row(step)

    def _delete_step(self, index: int) -> None:
        steps = self._collect_steps()
        if 0 <= index < len(steps):
            del steps[index]
            self._set_steps(steps)

    def _move_step(self, index: int, delta: int) -> None:
        new_index = index + delta
        if new_index < 0 or new_index >= len(self._step_rows):
            return
        steps = self._collect_steps()
        steps[index], steps[new_index] = steps[new_index], steps[index]
        self._set_steps(steps)

    def _collect_steps(self) -> list[NavigationStep]:
        return [row.to_step() for row in self._step_rows]

    def save(self) -> None:
        entry = self._selected_entry()
        if entry is None or self._profile_dir is None:
            self._status.configure(text="請先選關卡")
            return
        if not entry.is_user_copy:
            self._status.configure(text="範例不能直接存，請「從範例複製」")
            return
        try:
            navigation = NavigationScript(steps=self._collect_steps())
            path = save_navigation(self._profile_dir, navigation)
            self.reload()
            self._status.configure(text=f"已儲存 {path.name}")
        except Exception as exc:
            self._status.configure(text=translate_message(str(exc)))

    def _select_quest_in_menu(self, quest_id: str) -> None:
        for i, e in enumerate(self._entries):
            if e.quest_id == quest_id:
                self._profile_menu.set(list(self._profile_menu.cget("values"))[i])
                break

    def _create_blank(self) -> None:
        quest_id = self._new_id.get().strip()
        if not quest_id:
            self._status.configure(text="請輸入新關卡 ID")
            return
        try:
            create_blank_profile(quest_id, self._new_name.get().strip())
            self.reload_profiles()
            self._select_quest_in_menu(quest_id)
            self.reload()
            if self._on_quest_selected:
                self._on_quest_selected(quest_id)
            self._status.configure(text=f"已建立空白流程 {quest_id}，請用下方＋加步驟")
        except Exception as exc:
            self._status.configure(text=translate_message(str(exc)))

    def _copy_from_example(self) -> None:
        quest_id = self._new_id.get().strip()
        if not quest_id:
            self._status.configure(text="請輸入新關卡 ID")
            return
        try:
            copy_profile_to_user(quest_id)
            self.reload_profiles()
            self._select_quest_in_menu(quest_id)
            self.reload()
            if self._on_quest_selected:
                self._on_quest_selected(quest_id)
            self._status.configure(text=f"已從範例複製 {quest_id}，可改步驟或到預覽存圖示")
        except Exception as exc:
            self._status.configure(text=translate_message(str(exc)))

    def _apply_to_run(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            return
        if self._on_apply_quest:
            self._on_apply_quest(entry.quest_id)
            self._status.configure(text=f"已套用 {entry.quest_id}，請到「設定」按儲存")
