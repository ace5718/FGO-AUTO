"""Folder organization for user quest profiles (flow library)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from fgo_auto.run.run_config import ConfigError
from fgo_auto.services.paths import data_root
from fgo_auto.services.quest_flow_service import QuestProfileEntry, list_user_quest_profiles


class FlowFolder(BaseModel):
    id: str
    name: str


class FlowLibrary(BaseModel):
    folders: list[FlowFolder] = Field(default_factory=list)
    assignments: dict[str, str | None] = Field(default_factory=dict)


@dataclass(frozen=True)
class LibraryTreeItem:
    kind: str  # "folder" | "quest"
    item_id: str
    label: str
    quest: QuestProfileEntry | None = None
    folder_id: str | None = None


@dataclass(frozen=True)
class LibraryLayout:
    """Unassigned quests (no folder header) + folders with their quests."""

    unassigned: tuple[QuestProfileEntry, ...]
    folders: tuple[tuple[FlowFolder, tuple[QuestProfileEntry, ...]], ...]


def library_path() -> Path:
    return data_root() / "profiles" / "quests" / "library.yaml"


def load_library() -> FlowLibrary:
    path = library_path()
    if not path.is_file():
        return FlowLibrary()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return FlowLibrary.model_validate(data)


def save_library(library: FlowLibrary) -> Path:
    path = library_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(library.model_dump(mode="json"), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def _validate_folder_id(folder_id: str) -> None:
    if not re.fullmatch(r"[a-z][a-z0-9_]*", folder_id):
        raise ConfigError("資料夾 ID 請用小寫英文與底線，且以字母開頭")


def create_folder(folder_id: str, name: str) -> FlowLibrary:
    _validate_folder_id(folder_id)
    library = load_library()
    if any(f.id == folder_id for f in library.folders):
        raise ConfigError(f"資料夾已存在：{folder_id}")
    library.folders.append(FlowFolder(id=folder_id, name=name.strip() or folder_id))
    save_library(library)
    return library


def rename_folder(folder_id: str, name: str) -> FlowLibrary:
    library = load_library()
    for folder in library.folders:
        if folder.id == folder_id:
            folder.name = name.strip() or folder_id
            save_library(library)
            return library
    raise ConfigError(f"找不到資料夾：{folder_id}")


def delete_folder(folder_id: str) -> FlowLibrary:
    library = load_library()
    library.folders = [f for f in library.folders if f.id != folder_id]
    for quest_id, assigned in list(library.assignments.items()):
        if assigned == folder_id:
            library.assignments[quest_id] = None
    save_library(library)
    return library


def assign_quest_to_folder(quest_id: str, folder_id: str | None) -> FlowLibrary:
    library = load_library()
    if folder_id is not None and not any(f.id == folder_id for f in library.folders):
        raise ConfigError(f"找不到資料夾：{folder_id}")
    library.assignments[quest_id] = folder_id
    save_library(library)
    return library


def _group_entries(library: FlowLibrary, entries: list[QuestProfileEntry]) -> dict[str | None, list[QuestProfileEntry]]:
    assigned: dict[str | None, list[QuestProfileEntry]] = {None: []}
    for folder in library.folders:
        assigned[folder.id] = []
    for entry in entries:
        folder_id = library.assignments.get(entry.quest_id)
        if folder_id not in assigned:
            assigned[folder_id] = []
        assigned.setdefault(folder_id, []).append(entry)
    return assigned


def list_library_layout() -> LibraryLayout:
    library = load_library()
    entries = list_user_quest_profiles()
    grouped = _group_entries(library, entries)
    unassigned = tuple(
        sorted(grouped.get(None, []), key=lambda e: e.display_name or e.quest_id)
    )
    folders: list[tuple[FlowFolder, tuple[QuestProfileEntry, ...]]] = []
    for folder in library.folders:
        quests = tuple(
            sorted(grouped.get(folder.id, []), key=lambda e: e.display_name or e.quest_id)
        )
        folders.append((folder, quests))
    return LibraryLayout(unassigned=unassigned, folders=tuple(folders))


def list_library_tree() -> list[LibraryTreeItem]:
    """Flat list for legacy callers (no synthetic root folder)."""
    layout = list_library_layout()
    items: list[LibraryTreeItem] = []
    for entry in layout.unassigned:
        items.append(
            LibraryTreeItem(
                kind="quest",
                item_id=entry.quest_id,
                label=entry.display_name or entry.quest_id,
                quest=entry,
                folder_id=None,
            )
        )
    for folder, quests in layout.folders:
        items.append(
            LibraryTreeItem(
                kind="folder",
                item_id=folder.id,
                label=folder.name,
                folder_id=folder.id,
            )
        )
        for entry in quests:
            items.append(
                LibraryTreeItem(
                    kind="quest",
                    item_id=entry.quest_id,
                    label=f"  {entry.display_name or entry.quest_id}",
                    quest=entry,
                    folder_id=folder.id,
                )
            )
    return items
