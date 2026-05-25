from __future__ import annotations

from typing import Callable

import customtkinter as ctk
import tkinter as tk
from tkinter import simpledialog

from fgo_auto.services.flow_library import (
    assign_quest_to_folder,
    create_folder,
    delete_folder,
    list_library_layout,
    rename_folder,
)
from fgo_auto.services.quest_flow_service import QuestProfileEntry
from fgo_auto.ui.strings_zh import translate_message


class FlowLibraryPanel(ctk.CTkFrame):
    """Collapsible folder tree with drag-and-drop quest assignment."""

    def __init__(
        self,
        master,
        *,
        on_select: Callable[[str], None],
        on_changed: Callable[[], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(master, width=240, **kwargs)
        self._on_select = on_select
        self._on_changed = on_changed
        self._selected_quest: str | None = None
        self._selected_folder: str | None = None
        self._expanded: dict[str, bool] = {}
        self._drag_quest_id: str | None = None
        self._suppress_click = False
        self._drop_targets: dict[int, str | None] = {}
        self._quest_widgets: dict[int, str] = {}

        ctk.CTkLabel(self, text="流程列表", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", padx=8, pady=(8, 4)
        )
        ctk.CTkLabel(
            self,
            text="拖曳流程到資料夾；點 ▶/▼ 收合。未歸類流程顯示在頂部。",
            anchor="w",
            wraplength=220,
            font=ctk.CTkFont(size=11),
            text_color="#aaaaaa",
        ).pack(fill="x", padx=8, pady=(0, 4))

        tools = ctk.CTkFrame(self)
        tools.pack(fill="x", padx=6, pady=4)
        ctk.CTkButton(tools, text="＋資料夾", width=72, command=self._add_folder).pack(
            side="left", padx=2
        )
        ctk.CTkButton(tools, text="重新命名", width=72, command=self._rename_folder).pack(
            side="left", padx=2
        )
        ctk.CTkButton(tools, text="刪資料夾", width=72, fg_color="#8b3a3a", command=self._delete_folder).pack(
            side="left", padx=2
        )

        self._list_host = ctk.CTkScrollableFrame(self, width=220, height=360)
        self._list_host.pack(fill="both", expand=True, padx=6, pady=6)
        self._list_host.bind("<ButtonRelease-1>", self._on_global_release)

        self._status = ctk.CTkLabel(self, text="", anchor="w", wraplength=220, font=ctk.CTkFont(size=11))
        self._status.pack(fill="x", padx=8, pady=(0, 8))

        self.reload()

    def reload(self) -> None:
        for child in self._list_host.winfo_children():
            child.destroy()
        self._drop_targets.clear()
        self._quest_widgets.clear()

        layout = list_library_layout()

        if layout.unassigned:
            root_drop = ctk.CTkFrame(self._list_host, fg_color="transparent")
            root_drop.pack(fill="x", pady=(0, 4))
            self._register_drop_target(root_drop, None)
            for entry in layout.unassigned:
                self._add_quest_row(root_drop, entry, folder_id=None, indent=False)

        for folder, quests in layout.folders:
            self._expanded.setdefault(folder.id, True)
            block = ctk.CTkFrame(self._list_host, fg_color="transparent")
            block.pack(fill="x", pady=2)

            header = ctk.CTkFrame(block, fg_color="#2b2b2b")
            header.pack(fill="x")
            self._register_drop_target(header, folder.id)

            toggle = ctk.CTkButton(
                header,
                text="▼" if self._expanded[folder.id] else "▶",
                width=28,
                command=lambda fid=folder.id: self._toggle_folder(fid),
            )
            toggle.pack(side="left", padx=(2, 0), pady=2)

            name_btn = ctk.CTkButton(
                header,
                text=f"📁 {folder.name}",
                anchor="w",
                fg_color="transparent",
                hover_color="#3a3a3a",
                command=lambda fid=folder.id: self._select_folder(fid),
            )
            name_btn.pack(side="left", fill="x", expand=True, padx=2, pady=2)

            body = ctk.CTkFrame(block, fg_color="transparent")
            self._register_drop_target(body, folder.id)
            if self._expanded[folder.id]:
                body.pack(fill="x", padx=(12, 0))
                if quests:
                    for entry in quests:
                        self._add_quest_row(body, entry, folder_id=folder.id, indent=True)
                else:
                    ctk.CTkLabel(
                        body,
                        text="（拖曳流程到此）",
                        anchor="w",
                        text_color="#888888",
                        font=ctk.CTkFont(size=11),
                    ).pack(fill="x", padx=4, pady=2)

    def _register_drop_target(self, widget: tk.Misc, folder_id: str | None) -> None:
        self._drop_targets[id(widget)] = folder_id
        widget.bind("<Enter>", lambda _e, fid=folder_id: self._highlight_drop(fid))

    def _highlight_drop(self, folder_id: str | None) -> None:
        if self._drag_quest_id:
            label = "頂層（未歸類）" if folder_id is None else f"資料夾"
            self._status.configure(text=f"拖到{label}後放開以移入")

    def _add_quest_row(
        self,
        parent: ctk.CTkFrame,
        entry: QuestProfileEntry,
        *,
        folder_id: str | None,
        indent: bool,
    ) -> None:
        label = entry.display_name or entry.quest_id
        if indent:
            label = f"  {label}"
        row = ctk.CTkButton(
            parent,
            text=label,
            anchor="w",
            height=28,
            command=lambda qid=entry.quest_id: self._select_quest(qid),
        )
        row.pack(fill="x", pady=1)
        self._quest_widgets[id(row)] = entry.quest_id
        row.bind("<ButtonPress-1>", lambda e, qid=entry.quest_id: self._start_drag(e, qid))
        row.bind("<ButtonRelease-1>", self._on_global_release)

    def _start_drag(self, event: tk.Event, quest_id: str) -> None:
        self._drag_quest_id = quest_id
        self._selected_quest = quest_id
        self._status.configure(text=f"拖曳中：{quest_id}")

    def _folder_at(self, x_root: int, y_root: int) -> str | None | object:
        widget = self.winfo_containing(x_root, y_root)
        while widget is not None:
            wid = id(widget)
            if wid in self._drop_targets:
                return self._drop_targets[wid]
            if wid in self._quest_widgets:
                return "__quest__"
            widget = widget.master
        return "__miss__"

    def _on_global_release(self, event: tk.Event) -> None:
        if not self._drag_quest_id:
            return
        target = self._folder_at(event.x_root, event.y_root)
        quest_id = self._drag_quest_id
        self._drag_quest_id = None
        if target == "__miss__" or target == "__quest__":
            self._status.configure(text="已取消拖曳")
            return
        try:
            assign_quest_to_folder(quest_id, None if target is None else target)
            if isinstance(target, str):
                self._expanded[target] = True
            self._suppress_click = True
            self.reload()
            if self._on_changed:
                self._on_changed()
            if target is None:
                self._status.configure(text=f"已將 {quest_id} 移出資料夾")
            else:
                self._status.configure(text=f"已將 {quest_id} 移入資料夾")
            self._on_select(quest_id)
        except Exception as exc:
            self._status.configure(text=translate_message(str(exc)))

    def _toggle_folder(self, folder_id: str) -> None:
        self._expanded[folder_id] = not self._expanded.get(folder_id, True)
        self.reload()

    def _select_folder(self, folder_id: str) -> None:
        self._selected_folder = folder_id
        self._status.configure(text=f"已選資料夾：{folder_id}")

    def _select_quest(self, quest_id: str) -> None:
        if self._suppress_click:
            self._suppress_click = False
            return
        if self._drag_quest_id:
            return
        self._selected_quest = quest_id
        self._status.configure(text=f"已選流程：{quest_id}")
        self._on_select(quest_id)

    def _add_folder(self) -> None:
        parent = self.winfo_toplevel()
        folder_id = simpledialog.askstring("新增資料夾", "資料夾 ID（小寫英文底線）：", parent=parent)
        if not folder_id:
            return
        name = simpledialog.askstring("新增資料夾", "顯示名稱：", parent=parent) or folder_id
        try:
            create_folder(folder_id.strip(), name.strip())
            self._expanded[folder_id.strip()] = True
            self.reload()
            if self._on_changed:
                self._on_changed()
            self._status.configure(text=f"已新增資料夾 {folder_id}")
        except Exception as exc:
            self._status.configure(text=translate_message(str(exc)))

    def _rename_folder(self) -> None:
        if not self._selected_folder:
            self._status.configure(text="請先點選資料夾標題列")
            return
        parent = self.winfo_toplevel()
        name = simpledialog.askstring("重新命名", "新顯示名稱：", parent=parent)
        if not name:
            return
        try:
            rename_folder(self._selected_folder, name.strip())
            self.reload()
            self._status.configure(text="已重新命名資料夾")
        except Exception as exc:
            self._status.configure(text=translate_message(str(exc)))

    def _delete_folder(self) -> None:
        if not self._selected_folder:
            self._status.configure(text="請先點選要刪除的資料夾")
            return
        try:
            delete_folder(self._selected_folder)
            self._selected_folder = None
            self.reload()
            if self._on_changed:
                self._on_changed()
            self._status.configure(text="已刪除資料夾（內流程改為未歸類）")
        except Exception as exc:
            self._status.configure(text=translate_message(str(exc)))
