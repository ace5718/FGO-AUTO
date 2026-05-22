"""Load, edit, and save Quest navigation flows for the GUI flow editor."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from fgo_auto.quest.loader import load_navigation_script, load_quest_profile, resolve_quest_profile_dir
from fgo_auto.quest.models import (
    BattleScript,
    DelayStep,
    NavigationScript,
    NavigationStep,
    QuestProfile,
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


def load_flow(quest_id: str) -> tuple[QuestProfile, NavigationScript, Path]:
    profile, profile_dir = load_quest_profile(quest_id)
    nav_path = profile_dir / profile.navigation_script
    navigation = load_navigation_script(nav_path)
    return profile, navigation, profile_dir


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
    """Crop from last preview frame into data/profiles/quests/<id>/anchors/."""
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

    crop = frame[y1:y2, x1:x2]
    out = quest_anchors_dir(quest_id) / f"{name}.png"
    cv2.imwrite(str(out), crop)
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
    )
    save_profile(dest, profile)
    save_navigation(dest, NavigationScript(steps=[]))
    save_battle(dest, BattleScript())
    return dest


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
    return dest


def step_to_dict(step: NavigationStep) -> dict:
    return step.model_dump(mode="json")


def dict_to_step(data: dict) -> NavigationStep:
    action = data.get("action")
    if action == "tap_anchor":
        return TapAnchorStep.model_validate(data)
    if action == "scroll_until_anchor":
        return ScrollUntilAnchorStep.model_validate(data)
    if action == "wait_screen":
        return WaitScreenStep.model_validate(data)
    if action == "delay":
        return DelayStep.model_validate(data)
    if action == "run_subflow":
        return RunSubflowStep.model_validate(data)
    raise ConfigError(f"未知的步驟類型：{action!r}")


def _legacy_anchors_dir() -> Path:
    return data_root() / "anchors"


def anchor_png_path(profile_dir: Path, name: str) -> Path | None:
    if not name or name.startswith("（"):
        return None
    path = profile_dir / "anchors" / f"{name}.png"
    if path.is_file():
        return path
    legacy = _legacy_anchors_dir() / f"{name}.png"
    return legacy if legacy.is_file() else None


def list_saved_anchors(profile_dir: Path) -> list[str]:
    """PNG stems under <profile>/anchors/ for GUI pickers."""
    anchors_dir = profile_dir / "anchors"
    if not anchors_dir.is_dir():
        return []
    return sorted(p.stem for p in anchors_dir.glob("*.png") if p.is_file())


def anchor_choices_for_profile(profile_dir: Path, navigation: NavigationScript | None = None) -> list[str]:
    """Union of quest anchors/, legacy data/anchors/, and navigation step names."""
    names: set[str] = set(list_saved_anchors(profile_dir))
    legacy = _legacy_anchors_dir()
    if legacy.is_dir():
        for png in legacy.glob("*.png"):
            if png.name.startswith("_"):
                continue
            names.add(png.stem)
    if navigation is not None:
        for step in navigation.steps:
            if isinstance(step, (TapAnchorStep, ScrollUntilAnchorStep)):
                names.add(step.name)
    return sorted(names)


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


FLOW_GUIDE = (
    "① 新增/複製關卡→預覽存圖示→步驟選圖示（點右側縮圖看全圖）。②「執行」選流程套用→開始。\n"
    "② 列表要往下滑才看得到 → 用「往下滑找圖示」。③ 儲存後到「設定」儲存再執行。"
)

# GUI 顯示 ↔ YAML action
STEP_KIND_ZH: dict[str, str] = {
    "點擊": "tap_anchor",
    "往下滑找圖示": "scroll_until_anchor",
    "等待秒": "delay",
    "等待畫面": "wait_screen",
    "好友助戰": "run_subflow",
}

STEP_KIND_FROM_ACTION: dict[str, str] = {v: k for k, v in STEP_KIND_ZH.items()}

SCREEN_STATE_ZH: dict[str, str] = {
    "主畫面": "main",
    "關卡選單": "terminal",
    "戰鬥中": "battle",
    "結算": "result",
}

SCREEN_STATE_FROM_EN: dict[str, str] = {v: k for k, v in SCREEN_STATE_ZH.items()}
