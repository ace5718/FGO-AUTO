"""Load, edit, and save Quest navigation flows for the GUI flow editor."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from fgo_auto.quest.loader import load_navigation_script, load_quest_profile, resolve_quest_profile_dir
from fgo_auto.quest.models import (
    BattleScript,
    DelayStep,
    FriendSupportConfig,
    NavigationScript,
    NavigationStep,
    QuestProfile,
    RefreshUntilAnchorStep,
    RunSubflowStep,
    ScrollUntilAnchorStep,
    TapAnchorStep,
    WaitScreenStep,
)
from fgo_auto.run.run_config import ConfigError
from fgo_auto.services.paths import data_root, repo_root


@dataclass(frozen=True)
class QuestProfileEntry:
    quest_id: str
    display_name: str
    directory: Path
    is_user_copy: bool


def list_quest_profiles() -> list[QuestProfileEntry]:
    entries: list[QuestProfileEntry] = []
    seen: set[str] = set()
    for base, is_user in (
        (data_root() / "profiles" / "quests", True),
        (repo_root() / "examples" / "quests", False),
    ):
        if not base.is_dir():
            continue
        for child in sorted(base.iterdir()):
            if not child.is_dir():
                continue
            profile_path = child / "profile.yaml"
            if not profile_path.is_file():
                continue
            quest_id = child.name
            if quest_id in seen:
                continue
            seen.add(quest_id)
            data = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
            display_name = str(data.get("display_name") or quest_id)
            entries.append(
                QuestProfileEntry(
                    quest_id=quest_id,
                    display_name=display_name,
                    directory=child,
                    is_user_copy=is_user,
                )
            )
    return entries


def list_user_quest_profiles() -> list[QuestProfileEntry]:
    """Only data/profiles/quests/ — what the operator owns and can edit/delete."""
    return [e for e in list_quest_profiles() if e.is_user_copy]


def shared_anchor_resolutions() -> tuple[str, ...]:
    root = shared_anchors_dir()
    resolutions: list[str] = []
    for child in sorted(root.iterdir()):
        if child.is_dir() and re.fullmatch(r"\d+x\d+", child.name):
            resolutions.append(child.name)
    return tuple(resolutions)


def resolve_shared_anchor_path(name: str) -> Path | None:
    if not name or name.startswith("（"):
        return None
    root = shared_anchors_dir()
    if "/" in name:
        resolution, base = name.split("/", 1)
        candidate = root / resolution / f"{base}.png"
        return candidate if candidate.is_file() else None
    candidate = root / f"{name}.png"
    if candidate.is_file():
        return candidate
    matches: list[Path] = []
    for child in root.iterdir():
        if child.is_dir() and re.fullmatch(r"\d+x\d+", child.name):
            alt = child / f"{name}.png"
            if alt.is_file():
                matches.append(alt)
    if len(matches) == 1:
        return matches[0]
    return None


def list_shared_anchors(resolution: str | None = None) -> list[str]:
    root = shared_anchors_dir()
    names: list[str] = []
    if resolution and resolution != "全部":
        target = root / resolution
        if target.is_dir():
            for png in sorted(target.glob("*.png")):
                if png.is_file():
                    names.append(f"{resolution}/{png.stem}")
        return names
    for png in sorted(root.glob("*.png")):
        if png.is_file() and not png.name.startswith("_"):
            names.append(png.stem)
    for child in sorted(root.iterdir()):
        if child.is_dir() and re.fullmatch(r"\d+x\d+", child.name):
            for png in sorted(child.glob("*.png")):
                if png.is_file():
                    names.append(f"{child.name}/{png.stem}")
    return names


def list_example_quest_profiles() -> list[QuestProfileEntry]:
    """Read-only templates under examples/quests/ (for「從範例複製」only)."""
    return [e for e in list_quest_profiles() if not e.is_user_copy]


def load_flow(quest_id: str) -> tuple[QuestProfile, NavigationScript, Path]:
    profile, profile_dir = load_quest_profile(quest_id)
    nav_path = profile_dir / profile.navigation_script
    navigation = load_navigation_script(nav_path)
    return profile, navigation, profile_dir


# 流程分頁：主流程編排 vs 可重複使用的子流程
FLOW_KEYS: tuple[str, ...] = ("main", "enter_quest", "friend_support")
FLOW_LABELS: dict[str, str] = {
    "main": "主流程（編排）",
    "enter_quest": "進入關卡",
    "friend_support": "找好友",
}
RUNNABLE_SUBFLOWS: tuple[str, ...] = ("enter_quest", "friend_support")
SUBFLOW_LABELS_ZH: dict[str, str] = {
    "enter_quest": "進入關卡",
    "friend_support": "找好友",
}


def list_subflow_refs(profile_dir: Path) -> list[str]:
    """Subflow ids available for run_subflow (built-in + subflows/*.yaml)."""
    refs = list(RUNNABLE_SUBFLOWS)
    sf = profile_dir / "subflows"
    if sf.is_dir():
        for path in sorted(sf.glob("*.yaml")):
            if path.stem not in refs:
                refs.append(path.stem)
    return refs


@dataclass(frozen=True)
class SubflowPickerOption:
    """run_subflow ref (quest_id or subflows/*.yaml stem) + menu label."""

    ref: str
    label: str


def subflow_picker_options(current_quest_id: str | None = None) -> tuple[SubflowPickerOption, ...]:
    """Saved local quest profiles for「執行子流程」dropdown."""
    options: list[SubflowPickerOption] = []
    for entry in list_user_quest_profiles():
        if current_quest_id and entry.quest_id == current_quest_id:
            continue
        options.append(
            SubflowPickerOption(
                entry.quest_id,
                entry.display_name or entry.quest_id,
            )
        )
    return tuple(options)


def subflow_picker_choices(profile_dir: Path, current_quest_id: str | None = None) -> tuple[str, ...]:
    """GUI labels for subflow OptionMenu (saved 方案 + local subflows/*.yaml)."""
    del profile_dir  # kept for call-site compatibility
    labels = [o.label for o in subflow_picker_options(current_quest_id)]
    return tuple(labels)


def subflow_label_for_ref(ref: str) -> str:
    for entry in list_user_quest_profiles():
        if entry.quest_id == ref:
            return entry.display_name or entry.quest_id
    return SUBFLOW_LABELS_ZH.get(ref, ref)


def subflow_ref_from_label(label: str) -> str:
    for entry in list_user_quest_profiles():
        if (entry.display_name or entry.quest_id) == label:
            return entry.quest_id
    return next((k for k, v in SUBFLOW_LABELS_ZH.items() if v == label), label)


def subflows_dir(profile_dir: Path) -> Path:
    d = profile_dir / "subflows"
    d.mkdir(parents=True, exist_ok=True)
    return d


def subflow_path(profile_dir: Path, key: str) -> Path:
    if key == "main":
        return profile_dir / "navigation.yaml"
    return subflows_dir(profile_dir) / f"{key}.yaml"


def shared_anchors_dir() -> Path:
    d = data_root() / "anchors"
    d.mkdir(parents=True, exist_ok=True)
    return d


def shared_anchor_resolutions() -> tuple[str, ...]:
    root = shared_anchors_dir()
    resolutions: list[str] = []
    for child in sorted(root.iterdir()):
        if child.is_dir() and re.fullmatch(r"\d+x\d+", child.name):
            resolutions.append(child.name)
    return tuple(resolutions)


def resolve_shared_anchor_path(name: str, resolution: str | None = None) -> Path | None:
    if not name or name.startswith("（"):
        return None
    root = shared_anchors_dir()
    if "/" in name:
        resolution, base = name.split("/", 1)
        candidate = root / resolution / f"{base}.png"
        return candidate if candidate.is_file() else None
    if resolution and resolution != "全部":
        candidate = root / resolution / f"{name}.png"
        if candidate.is_file():
            return candidate
    candidate = root / f"{name}.png"
    if candidate.is_file():
        return candidate
    matches: list[Path] = []
    for child in root.iterdir():
        if child.is_dir() and re.fullmatch(r"\d+x\d+", child.name):
            alt = child / f"{name}.png"
            if alt.is_file():
                matches.append(alt)
    if len(matches) == 1:
        return matches[0]
    return None


def list_shared_anchors(resolution: str | None = None) -> list[str]:
    root = shared_anchors_dir()
    names: list[str] = []
    if resolution and resolution != "全部":
        target = root / resolution
        if target.is_dir():
            for png in sorted(target.glob("*.png")):
                if png.is_file():
                    names.append(f"{resolution}/{png.stem}")
        return names
    for png in sorted(root.glob("*.png")):
        if png.is_file() and not png.name.startswith("_"):
            names.append(png.stem)
    for child in sorted(root.iterdir()):
        if child.is_dir() and re.fullmatch(r"\d+x\d+", child.name):
            for png in sorted(child.glob("*.png")):
                if png.is_file():
                    names.append(f"{child.name}/{png.stem}")
    return names


def load_flow_script(profile_dir: Path, profile: QuestProfile, flow_key: str) -> NavigationScript:
    path = subflow_path(profile_dir, flow_key)
    if flow_key == "friend_support" and not path.is_file():
        return _friend_support_script_from_profile(profile)
    if not path.is_file():
        return NavigationScript(steps=[])
    return load_navigation_script(path)


def save_flow_script(profile_dir: Path, flow_key: str, navigation: NavigationScript) -> Path:
    path = subflow_path(profile_dir, flow_key)
    header = f"# {FLOW_LABELS.get(flow_key, flow_key)} — FGO-AUTO 流程設定\n"
    path.write_text(
        header + yaml.safe_dump(navigation.model_dump(mode="json"), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def load_subflow_script(
    profile_dir: Path,
    profile: QuestProfile,
    ref: str,
) -> tuple[NavigationScript | None, Path | None]:
    """Script + anchor profile_dir for run_subflow (local subflows/*.yaml or other 方案)."""
    local_path = subflows_dir(profile_dir) / f"{ref}.yaml"
    if local_path.is_file():
        return load_navigation_script(local_path), profile_dir
    try:
        _, navigation, other_dir = load_flow(ref)
        return navigation, other_dir
    except (ConfigError, OSError, ValueError):
        pass
    if ref == "friend_support" and profile.friend_support:
        return _friend_support_script_from_profile(profile), profile_dir
    return None, None


def _friend_support_script_from_profile(profile: QuestProfile) -> NavigationScript:
    if not profile.friend_support:
        return NavigationScript(steps=[])
    steps: list[NavigationStep] = []
    max_refresh = profile.friend_support.max_refresh_attempts
    for raw in profile.friend_support.steps:
        if "tap" in raw:
            steps.append(TapAnchorStep(name=str(raw["tap"])))
        elif raw.get("action") == "refresh_until_anchor":
            steps.append(
                RefreshUntilAnchorStep(
                    name=str(raw.get("name", "friend_target")),
                    max_attempts=int(raw.get("max_attempts", max_refresh)),
                )
            )
        elif raw.get("action") == "delay":
            steps.append(DelayStep(seconds=float(raw.get("seconds", 0.5))))
    return NavigationScript(steps=steps)


def default_enter_quest_script() -> NavigationScript:
    return NavigationScript(
        steps=[
            TapAnchorStep(name="chaldea_gate"),
            WaitScreenStep(state="main", timeout_s=10.0),
            TapAnchorStep(name="daily_quests"),
            TapAnchorStep(name="door_treasure_extreme"),
        ]
    )


def default_friend_support_script() -> NavigationScript:
    return NavigationScript(
        steps=[
            TapAnchorStep(name="friend_class_all"),
            RefreshUntilAnchorStep(name="friend_target", max_attempts=20),
        ]
    )


def default_main_orchestration_script() -> NavigationScript:
    return NavigationScript(
        steps=[
            RunSubflowStep(ref="enter_quest", repeat=1, interval_s=0.5),
            RunSubflowStep(ref="friend_support", repeat=1, interval_s=0.5),
            TapAnchorStep(name="party_slot_1"),
            TapAnchorStep(name="deploy_confirm"),
        ]
    )


def ensure_default_subflows(profile_dir: Path, profile: QuestProfile) -> None:
    subflows_dir(profile_dir)
    if not subflow_path(profile_dir, "main").is_file():
        save_flow_script(profile_dir, "main", default_main_orchestration_script())
    if not (subflows_dir(profile_dir) / "enter_quest.yaml").is_file():
        save_flow_script(profile_dir, "enter_quest", default_enter_quest_script())
    if not (subflows_dir(profile_dir) / "friend_support.yaml").is_file():
        save_flow_script(profile_dir, "friend_support", default_friend_support_script())


def save_navigation(profile_dir: Path, navigation: NavigationScript) -> Path:
    path = profile_dir / "navigation.yaml"
    payload = navigation.model_dump(mode="json")
    header = (
        "# 進關點擊流程 — 由 FGO-AUTO「流程設定」編輯\n"
        "# action: tap_anchor | scroll_until_anchor | wait_screen | delay | run_subflow\n"
    )
    path.write_text(
        header + yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def save_profile(profile_dir: Path, profile: QuestProfile) -> Path:
    path = profile_dir / "profile.yaml"
    path.write_text(
        yaml.safe_dump(profile.model_dump(mode="json"), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def quest_anchors_dir(quest_id: str, *, allow_example: bool = False) -> Path:
    """Return anchors/ for a quest; raises if profile is read-only example."""
    profile_dir = resolve_quest_profile_dir(quest_id)
    user_base = data_root() / "profiles" / "quests"
    if not allow_example and user_base not in profile_dir.parents:
        raise ConfigError("範例關卡不能存圖示，請在「流程設定」先「從範例複製」到本機")
    anchors = profile_dir / "anchors"
    anchors.mkdir(parents=True, exist_ok=True)
    return anchors


def save_quest_anchor_crop(
    quest_id: str,
    name: str,
    rect: tuple[int, int, int, int],
    *,
    frame_path: Path | None = None,
) -> Path:
    """Crop from last preview frame into per-quest anchors and shared resolution-specific library."""
    import cv2

    if not name.replace("_", "").isalnum():
        raise ConfigError("圖示名稱僅能使用英文、數字與底線")

    src = frame_path or (data_root() / "anchors" / "_last_frame_preview.png")
    if not src.is_file():
        raise ConfigError("請先在「預覽」按「擷圖」")

    frame = cv2.imread(str(src))
    if frame is None:
        raise ConfigError(f"無法讀取擷圖：{src}")

    x1, y1, x2, y2 = rect
    if x2 <= x1 or y2 <= y1:
        raise ConfigError("框選區域太小，請重新拖曳")

    h, w = frame.shape[:2]
    x1, y1 = max(0, min(x1, w - 1)), max(0, min(y1, h - 1))
    x2, y2 = max(x1 + 1, min(x2, w)), max(y1 + 1, min(y2, h))

    crop = frame[y1:y2, x1:x2]
    out = quest_anchors_dir(quest_id) / f"{name}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop)

    shared_dir = shared_anchors_dir() / f"{frame.shape[1]}x{frame.shape[0]}"
    shared_dir.mkdir(parents=True, exist_ok=True)
    shared_out = shared_dir / f"{name}.png"
    cv2.imwrite(str(shared_out), crop)
    return out


def _validate_quest_id(quest_id: str) -> None:
    if not quest_id.replace("_", "").isalnum():
        raise ConfigError("關卡 ID 僅能使用英文、數字與底線")


def _user_quest_dir(quest_id: str) -> Path:
    return data_root() / "profiles" / "quests" / quest_id


def save_battle(profile_dir: Path, battle: BattleScript) -> Path:
    path = profile_dir / "battle.yaml"
    path.write_text(
        yaml.safe_dump({"battle": battle.battle.model_dump(mode="json")}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def create_blank_profile(quest_id: str, display_name: str = "") -> Path:
    """Create an empty editable quest under data/profiles/quests/<id>/."""
    _validate_quest_id(quest_id)
    dest = _user_quest_dir(quest_id)
    if dest.exists():
        raise ConfigError(f"關卡已存在：{quest_id}")
    (dest / "anchors").mkdir(parents=True)

    profile = QuestProfile(
        quest_id=quest_id,
        display_name=display_name.strip() or quest_id,
        navigation_script="navigation.yaml",
        battle_script="battle.yaml",
        party_slot=1,
        friend_support=None,
    )
    save_profile(dest, profile)
    save_battle(dest, BattleScript())
    save_flow_script(dest, "main", NavigationScript(steps=[]))
    return dest


def delete_user_quest_profile(quest_id: str) -> None:
    """Remove a user copy under data/profiles/quests/ (not examples)."""
    _validate_quest_id(quest_id)
    dest = _user_quest_dir(quest_id)
    user_base = data_root() / "profiles" / "quests"
    if not dest.is_dir():
        raise ConfigError(f"找不到本機關卡：{quest_id}")
    if user_base not in dest.parents:
        raise ConfigError("範例關卡不能刪除，只能刪「·本機」的設定")
    import shutil

    shutil.rmtree(dest)


def copy_profile_to_user(quest_id: str, source_id: str = "treasure_door_extreme") -> Path:
    """Copy example quest into data/profiles/quests/<quest_id>/ for editing."""
    import shutil

    _validate_quest_id(quest_id)
    dest = _user_quest_dir(quest_id)
    if dest.exists():
        raise ConfigError(f"關卡已存在：{quest_id}")
    src = resolve_quest_profile_dir(source_id)
    shutil.copytree(src, dest)
    (dest / "anchors").mkdir(parents=True, exist_ok=True)
    profile, _ = load_quest_profile(quest_id)
    ensure_default_subflows(dest, profile)
    return dest


def step_to_dict(step: NavigationStep) -> dict:
    return step.model_dump(mode="json")


def dict_to_step(data: dict) -> NavigationStep:
    action = data.get("action")
    if action == "tap_anchor":
        return TapAnchorStep.model_validate(data)
    if action == "scroll_until_anchor":
        return ScrollUntilAnchorStep.model_validate(data)
    if action == "refresh_until_anchor":
        return RefreshUntilAnchorStep.model_validate(data)
    if action == "wait_screen":
        return WaitScreenStep.model_validate(data)
    if action == "delay":
        return DelayStep.model_validate(data)
    if action == "run_subflow":
        return RunSubflowStep.model_validate(data)
    raise ConfigError(f"未知的步驟類型：{action!r}")


def _legacy_anchors_dir() -> Path:
    return data_root() / "anchors"


def anchor_png_path(profile_dir: Path | None, name: str, resolution: str | None = None) -> Path | None:
    if not name or name.startswith("（"):
        return None
    if profile_dir is not None:
        quest_path = profile_dir / "anchors" / f"{name}.png"
        if quest_path.is_file():
            return quest_path
    return resolve_shared_anchor_path(name, resolution)


def list_saved_anchors(profile_dir: Path | None = None, resolution: str | None = None) -> list[str]:
    """Shared data/anchors/ plus optional per-quest overrides."""
    raw_names = list_shared_anchors(resolution)
    names: set[str] = set()
    for name in raw_names:
        if "/" in name:
            names.add(name.split("/", 1)[1])
        else:
            names.add(name)
    if profile_dir is not None:
        anchors_dir = profile_dir / "anchors"
        if anchors_dir.is_dir():
            for png in anchors_dir.glob("*.png"):
                if png.is_file():
                    names.add(png.stem)
    return sorted(names)


def delete_quest_anchor(
    name: str,
    *,
    profile_dir: Path | None = None,
    shared: bool = False,
) -> None:
    """Remove anchor PNG from shared library or quest anchors/."""
    if not name or name.startswith("（"):
        raise ConfigError("請選擇要刪除的圖示")
    if shared:
        path = resolve_shared_anchor_path(name)
        if path is None:
            raise ConfigError(f"找不到圖示檔：{name}")
    elif profile_dir is not None:
        path = profile_dir / "anchors" / f"{name}.png"
    else:
        raise ConfigError("請指定刪除共用或本關卡圖示")
    if not path.is_file():
        raise ConfigError(f"找不到圖示檔：{name}")
    path.unlink()


DEFAULT_FRIEND_SUPPORT_ANCHORS: tuple[str, ...] = (
    "friend_class_all",
    "friend_target",
    "friend_refresh",
)

# 檔名（程式用）→ 白話：好友支援列表畫面上的操作
FRIEND_SUPPORT_ANCHOR_ZH: dict[str, str] = {
    "friend_class_all": "選職階分頁（例如「全部」或你要的職階標籤）",
    "friend_target": "要找的好友那一列（框選禮裝或從者特徵，讓程式辨識）",
    "friend_refresh": "「更新」按鈕（列表沒有目標好友時重整）",
    # 舊版範例檔名（相容）
    "friend_list_open": "（舊）開啟好友支援列表",
    "friend_slot_1": "（舊）固定點第一位好友",
    "friend_confirm": "（舊）確認按鈕",
}

FRIEND_SUPPORT_FLOW_ZH = (
    "① 選職階　② 在列表找目標好友（看禮裝、從者）— 沒有就按「更新」重找（有次數上限）"
    "　③ 找到後點該好友　④ 之後由流程的編隊步驟繼續（如選隊伍槽、出擊）"
)

def default_friend_support_config() -> FriendSupportConfig:
    return FriendSupportConfig(
        max_refresh_attempts=20,
        steps=[
            {"tap": "friend_class_all"},
            {"action": "refresh_until_anchor", "name": "friend_target"},
        ],
    )


def ensure_friend_support_profile(
    profile_dir: Path,
    profile: QuestProfile,
    *,
    max_refresh_attempts: int = 20,
) -> QuestProfile:
    """Write default friend_support into profile.yaml if missing."""
    fs = default_friend_support_config().model_copy(update={"max_refresh_attempts": max_refresh_attempts})
    updated = profile.model_copy(update={"friend_support": fs})
    save_profile(profile_dir, updated)
    return updated


def save_friend_support_settings(
    profile_dir: Path,
    profile: QuestProfile,
    *,
    max_refresh_attempts: int,
) -> QuestProfile:
    """Persist friend_support steps + refresh limit (creates default steps if needed)."""
    if profile.friend_support and profile.friend_support.steps:
        fs = profile.friend_support.model_copy(update={"max_refresh_attempts": max_refresh_attempts})
    else:
        fs = default_friend_support_config().model_copy(update={"max_refresh_attempts": max_refresh_attempts})
    updated = profile.model_copy(update={"friend_support": fs})
    save_profile(profile_dir, updated)
    return updated


def navigation_uses_friend_support(navigation: NavigationScript) -> bool:
    return any(
        isinstance(step, RunSubflowStep) and step.ref == "friend_support"
        for step in navigation.steps
    )


def friend_support_anchor_plain(name: str) -> str:
    """User-facing description for a friend-support anchor id."""
    return FRIEND_SUPPORT_ANCHOR_ZH.get(
        name,
        f"自訂按鈕圖示（檔名 {name}）",
    )


def _friend_support_step_anchor_names(steps: list[dict[str, str | int | float]]) -> list[str]:
    names: list[str] = []
    needs_refresh = False
    for raw in steps:
        if "tap" in raw:
            names.append(str(raw["tap"]))
        elif raw.get("action") == "tap_anchor" and raw.get("name"):
            names.append(str(raw["name"]))
        elif raw.get("action") == "refresh_until_anchor" and raw.get("name"):
            names.append(str(raw["name"]))
            needs_refresh = True
    if needs_refresh and "friend_refresh" not in names:
        names.append("friend_refresh")
    return names


def friend_support_anchor_names(profile: QuestProfile) -> list[str]:
    """Anchor names required by friend_support in profile.yaml."""
    if profile.friend_support and profile.friend_support.steps:
        names = _friend_support_step_anchor_names(profile.friend_support.steps)
        if names:
            return names
    return list(DEFAULT_FRIEND_SUPPORT_ANCHORS)


def anchors_referenced_by_flow(
    profile: QuestProfile,
    navigation: NavigationScript,
) -> set[str]:
    """Anchor names used in navigation steps or friend_support taps."""
    refs = collect_anchor_names(profile, navigation)
    return set(refs)


def anchor_choices_for_profile(
    profile_dir: Path,
    navigation: NavigationScript | None = None,
    resolution: str | None = None,
) -> list[str]:
    """Union of shared anchors, quest anchors/, and step names."""
    names: set[str] = set(list_saved_anchors(profile_dir, resolution))
    if navigation is not None:
        for step in navigation.steps:
            if isinstance(step, (TapAnchorStep, ScrollUntilAnchorStep)):
                names.add(step.name)
    return sorted(names)


def is_profile_supported_for_resolution(profile_dir: Path, resolution: str | None = None) -> bool:
    """Return True if all anchors referenced by the profile exist for the chosen resolution."""
    resolution_arg = None if not resolution or resolution == "全部" else resolution
    try:
        profile, navigation, _ = load_flow(profile_dir.name)
    except Exception:
        return False
    for name in anchors_referenced_by_flow(profile, navigation):
        if anchor_png_path(profile_dir, name, resolution=resolution_arg) is None:
            return False
    return True


def shared_anchor_save_path(name: str, frame_path: Path) -> Path | None:
    """Return the shared anchor file path for a saved preview crop."""
    import cv2

    frame = cv2.imread(str(frame_path))
    if frame is None:
        return None
    resolution = f"{frame.shape[1]}x{frame.shape[0]}"
    return shared_anchors_dir() / resolution / f"{name}.png"


def collect_anchor_names(profile: QuestProfile, navigation: NavigationScript) -> list[str]:
    names: list[str] = []
    for step in navigation.steps:
        if isinstance(step, (TapAnchorStep, ScrollUntilAnchorStep)):
            names.append(step.name)
    if profile.friend_support:
        for raw in profile.friend_support.steps:
            if "tap" in raw:
                names.append(raw["tap"])
    return names


FRIEND_SUPPORT_TOOLTIP = (
    "執行已存好的「找好友」子流程（選職階、更新重找、點好友）。"
    "內容在 subflows/friend_support.yaml，可從範例複製後修改。"
)

FRIEND_SUPPORT_SETUP_INTRO = "請在「圖示庫」下方啟用並儲存好友設定，再到「預覽」存三張小圖。"

FLOW_GUIDE = (
    "① 編排主流程；用「執行子流程」選其他已存本機方案，可設次數與間隔。\n"
    "② 各方案的主流程在 navigation.yaml；片段檔在 subflows/*.yaml（相容舊 ref）。\n"
    "③ 圖示存「預覽」或「共用圖示庫」（比對支援約 ±15% 縮放）；列表往下拉用「往下滑找圖示」。"
)

# GUI 顯示 ↔ YAML action
STEP_KINDS_MAIN: dict[str, str] = {
    "執行子流程": "run_subflow",
    "點擊": "tap_anchor",
    "往下滑找圖示": "scroll_until_anchor",
    "等待秒": "delay",
    "等待畫面": "wait_screen",
}

STEP_KINDS_SUBFLOW: dict[str, str] = {
    "點擊": "tap_anchor",
    "往下滑找圖示": "scroll_until_anchor",
    "更新重找圖示": "refresh_until_anchor",
    "等待秒": "delay",
    "等待畫面": "wait_screen",
}

# 向後相容
STEP_KIND_ZH = STEP_KINDS_SUBFLOW | {"執行子流程": "run_subflow", "好友助戰": "run_subflow"}

STEP_KIND_FROM_ACTION: dict[str, str] = {v: k for k, v in STEP_KIND_ZH.items()}

SCREEN_STATE_ZH: dict[str, str] = {
    "主畫面": "main",
    "關卡選單": "terminal",
    "戰鬥中": "battle",
    "結算": "result",
}

SCREEN_STATE_FROM_EN: dict[str, str] = {v: k for k, v in SCREEN_STATE_ZH.items()}
