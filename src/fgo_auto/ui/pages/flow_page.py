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
    RefreshUntilAnchorStep,
    RunSubflowStep,
    ScrollUntilAnchorStep,
    TapAnchorStep,
    TapCoordinateStep,
    WaitScreenStep,
)
from fgo_auto.services.quest_flow_service import (
    delete_user_quest_profile,
    FLOW_GUIDE,
    SCREEN_STATE_ZH,
    STEP_KINDS_MAIN,
    STEP_KINDS_SUBFLOW,
    shared_anchor_resolutions,
    subflow_label_for_ref,
    subflow_picker_choices,
    subflow_ref_from_label,
    QuestProfileEntry,
    anchor_choices_for_profile,
    anchor_png_path,
    copy_profile_to_user,
    create_blank_profile,
    ensure_default_subflows,
    list_example_quest_profiles,
    list_user_quest_profiles,
    load_flow,
    load_flow_script,
    load_quest_profile,
    save_flow_script,
    save_profile,
)
from fgo_auto.ui.strings_zh import translate_message
from fgo_auto.ui.widgets.anchor_preview_dialog import show_anchor_fullsize
from fgo_auto.ui.widgets.coordinate_pick_dialog import pick_coordinate_on_capture

_NO_ANCHOR = "（尚無圖示，請到預覽／共用圖示庫新增）"
_SCROLL_ATTEMPTS = ("5", "8", "10", "12", "15")
_SCREEN_CHOICES = tuple(SCREEN_STATE_ZH.keys())
_THUMB_SIZE = (100, 64)


def _pil_anchor_thumb(path: Path) -> Image.Image:
    """Load anchor PNG for display (RGBA flattened; same path as preview page)."""
    img = Image.open(path)
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (48, 48, 48))
        bg.paste(img, mask=img.split()[3])
        return bg
    return img.convert("RGB")


def _load_anchor_photo(profile_dir: Path | None, name: str, resolution: str = "全部") -> ImageTk.PhotoImage | None:
    if profile_dir is None:
        return None
    resolution_arg = None if resolution == "全部" else resolution
    path = anchor_png_path(profile_dir, name, resolution=resolution_arg)
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
        *,
        on_delete: Callable[[], None],
        on_move: Callable[[int], None],
        step_kinds: dict[str, str],
        subflow_choices: tuple[str, ...] = (),
        shared_anchor_resolution: str = "全部",
        on_pick_coordinate: Callable[[], tuple[int, int] | None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._anchor_choices = anchor_choices or [_NO_ANCHOR]
        self._profile_dir = profile_dir
        self._step_kinds = step_kinds
        self._subflow_choices = subflow_choices or ("（尚無其他本機方案）",)
        self._shared_anchor_resolution = shared_anchor_resolution
        self._on_pick_coordinate = on_pick_coordinate
        self._thumb_photo: ImageTk.PhotoImage | None = None

        kinds = list(step_kinds.keys())
        self._kind_menu = ctk.CTkOptionMenu(self, values=kinds, width=120, command=self._on_kind)
        self._kind_menu.pack(side="left", padx=4, pady=6)

        self._detail = ctk.CTkFrame(self)
        self._detail.pack(side="left", padx=4)
        self._pickers: dict[str, ctk.CTkOptionMenu] = {}
        self._entries: dict[str, ctk.CTkEntry] = {}

        self._thumb_box = ctk.CTkFrame(self, width=_THUMB_SIZE[0] + 4, height=_THUMB_SIZE[1] + 4)
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

    def _set_thumb_visible(self, visible: bool) -> None:
        if visible:
            if not self._thumb_box.winfo_ismapped():
                self._thumb_box.pack(side="left", padx=6, pady=4)
        else:
            self._thumb_box.pack_forget()

    def _clear_detail(self) -> None:
        for child in self._detail.winfo_children():
            child.destroy()
        self._pickers.clear()
        self._entries.clear()

    def _show_thumb(self, name: str | None) -> None:
        if not name:
            self._thumb_photo = None
            self._thumb_lbl.configure(image="", text="—")
            return
        photo = _load_anchor_photo(self._profile_dir, name, resolution=self._shared_anchor_resolution)
        if photo is None:
            self._thumb_photo = None
            self._thumb_lbl.configure(image="", text="無圖")
            return
        self._thumb_photo = photo
        self._thumb_lbl.configure(image=photo, text="")

    def set_shared_anchor_resolution(self, resolution: str) -> None:
        self._shared_anchor_resolution = resolution
        if "anchor" in self._pickers:
            self._show_thumb(self._pick("anchor"))

    def _open_full_image(self) -> None:
        if self._kind_menu.get() not in ("點擊", "往下滑找圖示", "更新重找圖示"):
            return
        name = self._pick("anchor") if "anchor" in self._pickers else None
        if name and not name.startswith("（"):
            show_anchor_fullsize(
                self.winfo_toplevel(),
                self._profile_dir,
                name,
                resolution=self._shared_anchor_resolution,
            )

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
        if key in self._entries:
            return self._entries[key].get().strip()
        return self._pickers[key].get().strip()

    def _add_seconds_entry(self, seconds: float) -> None:
        row = ctk.CTkFrame(self._detail)
        row.pack(fill="x", pady=1)
        ctk.CTkLabel(row, text="秒數", width=52, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(row, width=72, placeholder_text="例如 1.5")
        entry.insert(0, str(seconds))
        entry.pack(side="left")
        self._entries["seconds"] = entry

    def _add_coordinate_entries(self, x: int, y: int) -> None:
        row = ctk.CTkFrame(self._detail)
        row.pack(fill="x", pady=1)
        ctk.CTkLabel(row, text="X", width=28, anchor="w").pack(side="left")
        x_entry = ctk.CTkEntry(row, width=72, placeholder_text="0")
        x_entry.insert(0, str(x))
        x_entry.pack(side="left", padx=(0, 8))
        ctk.CTkLabel(row, text="Y", width=28, anchor="w").pack(side="left")
        y_entry = ctk.CTkEntry(row, width=72, placeholder_text="0")
        y_entry.insert(0, str(y))
        y_entry.pack(side="left")
        self._entries["x"] = x_entry
        self._entries["y"] = y_entry

    def _parse_seconds(self) -> float:
        raw = self._pick("seconds")
        if not raw:
            raise ValueError("請輸入等待秒數")
        try:
            value = float(raw)
        except ValueError as exc:
            raise ValueError("秒數請輸入數字（可含小數）") from exc
        if value < 0:
            raise ValueError("秒數不可為負數")
        return value

    def _pick_coordinate(self) -> None:
        if self._on_pick_coordinate is None:
            return
        coords = self._on_pick_coordinate()
        if coords is None:
            return
        if "x" in self._entries:
            self._entries["x"].delete(0, "end")
            self._entries["x"].insert(0, str(coords[0]))
        if "y" in self._entries:
            self._entries["y"].delete(0, "end")
            self._entries["y"].insert(0, str(coords[1]))

    def _parse_coordinate(self, key: str) -> int:
        raw = self._pick(key)
        if not raw:
            raise ValueError(f"請輸入 {key.upper()} 座標")
        try:
            value = int(raw)
        except ValueError as exc:
            raise ValueError(f"{key.upper()} 座標請輸入整數") from exc
        if value < 0:
            raise ValueError(f"{key.upper()} 座標不可為負數")
        return value

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
        elif isinstance(step, TapCoordinateStep):
            self._kind_menu.set("點擊座標")
            self._on_kind("點擊座標")
            if "x" in self._entries:
                self._entries["x"].delete(0, "end")
                self._entries["x"].insert(0, str(step.x))
            if "y" in self._entries:
                self._entries["y"].delete(0, "end")
                self._entries["y"].insert(0, str(step.y))
        elif isinstance(step, ScrollUntilAnchorStep):
            self._kind_menu.set("往下滑找圖示")
            self._on_kind("往下滑找圖示")
            self._set_pick("anchor", step.name, tuple(self._anchor_choices))
            self._set_pick("attempts", str(step.max_attempts), _SCROLL_ATTEMPTS)
            self._show_thumb(step.name)
        elif isinstance(step, DelayStep):
            self._kind_menu.set("等待秒")
            self._on_kind("等待秒")
            if "seconds" in self._entries:
                self._entries["seconds"].delete(0, "end")
                self._entries["seconds"].insert(0, str(step.seconds))
        elif isinstance(step, WaitScreenStep):
            self._kind_menu.set("等待畫面")
            self._on_kind("等待畫面")
            zh = next((k for k, v in SCREEN_STATE_ZH.items() if v == step.state), "主畫面")
            self._set_pick("screen", zh, _SCREEN_CHOICES)
        elif isinstance(step, RefreshUntilAnchorStep):
            self._kind_menu.set("更新重找圖示")
            self._on_kind("更新重找圖示")
            self._set_pick("anchor", step.name, tuple(self._anchor_choices))
            self._set_pick("attempts", str(step.max_attempts), _SCROLL_ATTEMPTS)
        elif isinstance(step, RunSubflowStep):
            self._kind_menu.set("執行子流程")
            self._on_kind("執行子流程")
            ref_zh = subflow_label_for_ref(step.ref)
            choices = self._subflow_choices
            if ref_zh not in choices:
                choices = (ref_zh,) + tuple(c for c in choices if c != ref_zh)
            self._set_pick("subflow", ref_zh, choices)
            if "repeat" in self._entries:
                self._entries["repeat"].delete(0, "end")
                self._entries["repeat"].insert(0, str(step.repeat))
            if "interval" in self._entries:
                self._entries["interval"].delete(0, "end")
                self._entries["interval"].insert(0, str(step.interval_s))

    def _on_kind(self, kind: str) -> None:
        self._clear_detail()
        if kind in ("點擊", "往下滑找圖示"):
            self._set_thumb_visible(True)
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
            self._set_thumb_visible(False)
            self._add_seconds_entry(1.0)
        elif kind == "等待畫面":
            self._set_thumb_visible(False)
            self._add_picker("screen", "畫面", _SCREEN_CHOICES)
        elif kind == "點擊座標":
            self._set_thumb_visible(False)
            self._add_coordinate_entries(0, 0)
            if self._on_pick_coordinate is not None:
                row = ctk.CTkFrame(self._detail)
                row.pack(fill="x", pady=1)
                ctk.CTkButton(row, text="從擷圖點選", width=96, command=self._pick_coordinate).pack(
                    side="left"
                )
        elif kind == "更新重找圖示":
            self._set_thumb_visible(True)
            self._add_picker(
                "anchor",
                "目標圖示",
                tuple(self._anchor_choices),
                on_change=self._on_anchor_pick,
            )
            self._on_anchor_pick(self._pickers["anchor"].get())
            self._add_picker("attempts", "更新次數", _SCROLL_ATTEMPTS, width=72)
        elif kind == "執行子流程":
            self._set_thumb_visible(False)
            row = ctk.CTkFrame(self._detail)
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text="方案", width=52, anchor="w").pack(side="left")
            menu = ctk.CTkOptionMenu(row, values=list(self._subflow_choices), width=180)
            first = self._subflow_choices[0] if self._subflow_choices else "（尚無其他本機方案）"
            menu.set(first)
            menu.pack(side="left")
            self._pickers["subflow"] = menu
            r2 = ctk.CTkFrame(self._detail)
            r2.pack(fill="x", pady=1)
            ctk.CTkLabel(r2, text="次數", width=52, anchor="w").pack(side="left")
            rep = ctk.CTkEntry(r2, width=48)
            rep.insert(0, "1")
            rep.pack(side="left", padx=(0, 8))
            self._entries["repeat"] = rep
            ctk.CTkLabel(r2, text="間隔秒", width=52, anchor="w").pack(side="left")
            iv = ctk.CTkEntry(r2, width=48)
            iv.insert(0, "0.5")
            iv.pack(side="left")
            self._entries["interval"] = iv

    def _resolve_anchor_name(self) -> str:
        name = self._pick("anchor")
        if not name or name.startswith("（"):
            raise ValueError("請從下拉選擇圖示，或先到預覽儲存圖示")
        return name

    def to_step(self) -> NavigationStep:
        kind = self._kind_menu.get()
        action = self._step_kinds[kind]
        if action == "tap_anchor":
            return TapAnchorStep(name=self._resolve_anchor_name())
        if action == "scroll_until_anchor":
            return ScrollUntilAnchorStep(
                name=self._resolve_anchor_name(),
                max_attempts=int(self._pick("attempts")),
            )
        if action == "refresh_until_anchor":
            return RefreshUntilAnchorStep(
                name=self._resolve_anchor_name(),
                max_attempts=int(self._pick("attempts")),
            )
        if action == "delay":
            return DelayStep(seconds=self._parse_seconds())
        if action == "tap_coordinate":
            return TapCoordinateStep(x=self._parse_coordinate("x"), y=self._parse_coordinate("y"))
        if action == "wait_screen":
            return WaitScreenStep(state=SCREEN_STATE_ZH[self._pick("screen")], timeout_s=15.0)
        ref_zh = self._pick("subflow")
        ref = subflow_ref_from_label(ref_zh)
        return RunSubflowStep(
            ref=ref,
            repeat=max(1, int(float(self._pick("repeat") or "1"))),
            interval_s=float(self._pick("interval") or "0.5"),
        )


class FlowPage(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_apply_quest_profile: Callable[[str], None] | None = None,
        on_quest_selected: Callable[[str], None] | None = None,
        on_resolution_change: Callable[[str], None] | None = None,
        on_profiles_changed: Callable[[], None] | None = None,
        on_capture: Callable[[], Path] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_apply_quest = on_apply_quest_profile
        self._on_quest_selected = on_quest_selected
        self._on_resolution_change = on_resolution_change
        self._on_profiles_changed = on_profiles_changed
        self._on_capture = on_capture
        self._entries: list[QuestProfileEntry] = []
        self._profile_dir: Path | None = None
        self._profile: QuestProfile | None = None
        self._anchor_choices: list[str] = [_NO_ANCHOR]
        self._subflow_choices: tuple[str, ...] = ()
        self._step_rows: list[_StepRow] = []
        self._shared_anchor_resolution: str = "全部"

        ctk.CTkLabel(self, text=FLOW_GUIDE, justify="left", wraplength=880).pack(
            anchor="w", padx=12, pady=(10, 4)
        )

        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(top, text="方案", width=40).pack(side="left")
        self._profile_menu = ctk.CTkOptionMenu(top, values=["…"], width=200, command=self._on_profile_pick)
        self._profile_menu.pack(side="left", padx=4)
        ctk.CTkLabel(top, text="顯示名稱", width=72).pack(side="left", padx=(12, 0))
        self._display_name = ctk.CTkEntry(top, width=240, placeholder_text="可編輯顯示名稱")
        self._display_name.pack(side="left", padx=4)
        ctk.CTkButton(top, text="更新名稱", width=88, command=self._save_display_name).pack(side="left", padx=4)
        ctk.CTkLabel(top, text="解析度", width=56).pack(side="left", padx=(12, 0))
        self._resolution_menu = ctk.CTkOptionMenu(top, values=("全部",), width=140, command=self._on_resolution_change)
        self._resolution_menu.pack(side="left", padx=4)
        ctk.CTkButton(top, text="儲存", width=56, command=self.save).pack(side="left", padx=4)
        ctk.CTkButton(top, text="重新載入", width=72, command=self.reload).pack(side="left", padx=4)

        copy_row = ctk.CTkFrame(self)
        copy_row.pack(fill="x", padx=12, pady=2)
        self._new_id = ctk.CTkEntry(copy_row, placeholder_text="新方案 ID（英文底線）", width=160)
        self._new_id.pack(side="left", padx=(0, 6))
        self._new_name = ctk.CTkEntry(copy_row, placeholder_text="顯示名稱（可選）", width=120)
        self._new_name.pack(side="left", padx=(0, 6))
        ctk.CTkButton(copy_row, text="新增空白方案", width=100, command=self._create_blank).pack(side="left", padx=2)
        ctk.CTkButton(
            copy_row,
            text="刪除本機關卡",
            width=100,
            fg_color="#8b3a3a",
            command=self._delete_user_quest,
        ).pack(side="left", padx=2)

        self._steps_host = ctk.CTkScrollableFrame(
            self, height=280, label_text="主流程（用「執行子流程」選其他本機方案）"
        )
        self._steps_host.pack(fill="both", expand=True, padx=12, pady=4)

        add_row = ctk.CTkFrame(self)
        add_row.pack(fill="x", padx=12, pady=4)
        ctk.CTkButton(add_row, text="＋點擊", width=72, command=self._add_tap).pack(side="left", padx=2)
        ctk.CTkButton(add_row, text="＋點擊座標", width=96, command=self._add_coordinate).pack(side="left", padx=2)
        ctk.CTkButton(add_row, text="＋往下滑找", width=96, command=self._add_scroll).pack(side="left", padx=2)
        ctk.CTkButton(add_row, text="＋等待", width=72, command=lambda: self._add_step(DelayStep(seconds=0.5))).pack(
            side="left", padx=2
        )
        ctk.CTkButton(add_row, text="＋子流程", width=80, command=self._add_subflow_step).pack(side="left", padx=2)

        self._status = ctk.CTkLabel(self, text="", anchor="w", wraplength=880)
        self._status.pack(fill="x", padx=12, pady=6)

        self.reload_profiles()

    def _default_anchor(self) -> str:
        if self._anchor_choices and self._anchor_choices[0] != _NO_ANCHOR:
            return self._anchor_choices[0]
        return "chaldea_gate"

    def refresh_anchor_choices(self) -> None:
        """Refresh step anchor dropdowns after 圖示庫 or 預覽 changes."""
        if self._profile_dir is None:
            return
        steps = self._collect_steps() if self._step_rows else []
        nav = NavigationScript(steps=steps) if steps else None
        self._anchor_choices = anchor_choices_for_profile(
            self._profile_dir,
            nav,
            resolution=self._shared_anchor_resolution,
        )
        if not self._anchor_choices:
            self._anchor_choices = [_NO_ANCHOR]

    def _resolution_values(self) -> tuple[str, ...]:
        return ("全部", *shared_anchor_resolutions())

    def _update_resolution_menu(self) -> None:
        values = list(self._resolution_values())
        self._resolution_menu.configure(values=values)
        if self._shared_anchor_resolution in values:
            self._resolution_menu.set(self._shared_anchor_resolution)
        else:
            self._shared_anchor_resolution = values[0]
            self._resolution_menu.set(self._shared_anchor_resolution)

    def _on_resolution_change(self, selected: str) -> None:
        self.set_shared_anchor_resolution(selected)
        if self._on_resolution_change:
            self._on_resolution_change(selected)

    def set_shared_anchor_resolution(self, resolution: str) -> None:
        self._shared_anchor_resolution = resolution
        self._update_resolution_menu()

        if self._profile_dir is not None:
            steps = self._collect_steps() if self._step_rows else []
            nav = NavigationScript(steps=steps) if steps else None
            self._anchor_choices = anchor_choices_for_profile(
                self._profile_dir,
                nav,
                resolution=self._shared_anchor_resolution,
            )
            if not self._anchor_choices:
                self._anchor_choices = [_NO_ANCHOR]

        for row in self._step_rows:
            row.set_shared_anchor_resolution(self._shared_anchor_resolution)
            if "anchor" in row._pickers:
                menu = row._pickers["anchor"]
                cur = menu.get()
                opts = list(self._anchor_choices)
                menu.configure(values=opts)
                if cur in opts:
                    menu.set(cur)
                elif opts:
                    menu.set(opts[0])

    def _pick_coordinate_for_step(self) -> tuple[int, int] | None:
        if self._on_capture is None:
            return None
        return pick_coordinate_on_capture(self.winfo_toplevel(), self._on_capture)

    def _add_tap(self) -> None:
        self._add_step(TapAnchorStep(name=self._default_anchor()))

    def _add_scroll(self) -> None:
        self._add_step(ScrollUntilAnchorStep(name=self._default_anchor(), max_attempts=8))

    def _add_coordinate(self) -> None:
        if self._on_capture is not None:
            coords = pick_coordinate_on_capture(self.winfo_toplevel(), self._on_capture)
            if coords is not None:
                self._add_step(TapCoordinateStep(x=coords[0], y=coords[1]))
                return
        self._add_step(TapCoordinateStep(x=0, y=0))

    def _add_subflow_step(self) -> None:
        entry = self._selected_entry()
        choices = subflow_picker_choices(
            self._profile_dir or Path(),
            current_quest_id=entry.quest_id if entry else None,
        )
        if not choices or choices[0].startswith("（"):
            self._status.configure(text="請先建立第二個本機方案，再編排子流程")
            return
        ref = subflow_ref_from_label(choices[0])
        self._add_step(RunSubflowStep(ref=ref, repeat=1, interval_s=0.5))

    def reload_profiles(self) -> None:
        self._entries = list_user_quest_profiles()
        self._update_resolution_menu()
        if not self._entries:
            self._profile_menu.configure(values=["（尚無本機方案）"])
            self._profile_dir = None
            self._clear_steps()
            self._status.configure(text="請新增本機方案開始")
            return
        labels = [f"{e.display_name or e.quest_id}" for e in self._entries]
        self._profile_menu.configure(values=labels)
        self._profile_menu.set(labels[0])
        if self._on_profiles_changed:
            self._on_profiles_changed()
        self.reload()

    def _selected_entry(self) -> QuestProfileEntry | None:
        if not self._entries:
            return None
        label = self._profile_menu.get()
        values = list(self._profile_menu.cget("values"))
        if label not in values:
            return None
        idx = values.index(label)
        return self._entries[idx]

    def _save_display_name(self) -> None:
        entry = self._selected_entry()
        if entry is None or self._profile_dir is None:
            self._status.configure(text="請先選本機方案")
            return
        display_name = self._display_name.get().strip()
        if not display_name:
            self._status.configure(text="請輸入顯示名稱")
            return
        try:
            profile, _ = load_quest_profile(entry.quest_id)
            profile.display_name = display_name
            save_profile(self._profile_dir, profile)
            self.reload_profiles()
            self._select_quest_in_menu(entry.quest_id)
            self.reload()
            self._status.configure(text=f"已更新顯示名稱為「{display_name}」。")
        except Exception as exc:
            self._status.configure(text=translate_message(str(exc)))

    def _on_profile_pick(self, _label: str) -> None:
        self.reload()

    def reload(self) -> None:
        self._update_resolution_menu()
        entry = self._selected_entry()
        if entry is None:
            return
        try:
            profile, navigation, profile_dir = load_flow(entry.quest_id)
            if entry.is_user_copy:
                ensure_default_subflows(profile_dir, profile)
            self._profile_dir = profile_dir
            self._profile = profile
            self._subflow_choices = subflow_picker_choices(
                profile_dir, current_quest_id=entry.quest_id
            )
            self._anchor_choices = anchor_choices_for_profile(
                profile_dir,
                navigation,
                resolution=self._shared_anchor_resolution,
            )
            if not self._anchor_choices:
                self._anchor_choices = [_NO_ANCHOR]
            self._set_steps(navigation.steps)
            self._display_name.delete(0, tk.END)
            self._display_name.insert(0, entry.display_name or entry.quest_id)
            self._status.configure(
                text=f"{entry.quest_id}　共用圖示庫 + 本關卡 anchors/"
            )
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
            step_kinds=STEP_KINDS_MAIN,
            subflow_choices=self._subflow_choices,
            shared_anchor_resolution=self._shared_anchor_resolution,
            on_pick_coordinate=self._pick_coordinate_for_step,
        )
        row.pack(fill="x", pady=2)
        self._step_rows.append(row)

    def _add_step(self, step: NavigationStep) -> None:
        if self._selected_entry() is None or self._profile_dir is None:
            self._status.configure(text="請先選本機方案，或新增本機方案")
            return
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
            self._status.configure(text="範例不能直接存，請先建立本機方案")
            return
        try:
            navigation = NavigationScript(steps=self._collect_steps())
            path = save_flow_script(self._profile_dir, "main", navigation)
            self.reload()
            self._status.configure(text=f"已儲存主流程（{path.name}）")
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
            if self._on_profiles_changed:
                self._on_profiles_changed()
        except Exception as exc:
            self._status.configure(text=translate_message(str(exc)))

    def _delete_user_quest(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            self._status.configure(text="請先選要刪除的方案")
            return
        if not entry.is_user_copy:
            self._status.configure(text="範例（·範例）不能刪除")
            return
        from tkinter import messagebox

        if not messagebox.askyesno(
            "刪除方案",
            f"確定刪除本機方案「{entry.quest_id}」？\n"
            f"會刪除整個資料夾：\n{entry.directory}",
            parent=self.winfo_toplevel(),
        ):
            return
        try:
            delete_user_quest_profile(entry.quest_id)
            self._profile_dir = None
            self._clear_steps()
            self.reload_profiles()
            self._status.configure(text=f"已刪除 {entry.quest_id}")
        except Exception as exc:
            self._status.configure(text=translate_message(str(exc)))

    def _copy_from_example(self) -> None:
        quest_id = self._new_id.get().strip()
        if not quest_id:
            self._status.configure(text="請輸入新方案 ID")
            return
        examples = list_example_quest_profiles()
        if not examples:
            self._status.configure(text="找不到範例方案")
            return
        source = examples[0]
        try:
            copy_profile_to_user(quest_id, source_id=source.quest_id)
            self.reload_profiles()
            self._select_quest_in_menu(quest_id)
            self.reload()
            if self._on_quest_selected:
                self._on_quest_selected(quest_id)
            src = source.display_name or source.quest_id
            self._status.configure(text=f"已從範例「{src}」複製為 {quest_id}，可改步驟或到預覽存圖示")
            if self._on_profiles_changed:
                self._on_profiles_changed()
        except Exception as exc:
            self._status.configure(text=translate_message(str(exc)))

    def _apply_to_run(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            return
        if self._on_apply_quest:
            self._on_apply_quest(entry.quest_id)
            self._status.configure(text=f"已套用 {entry.quest_id}，請到「設定」按「儲存至本機」寫入 run.yaml")
