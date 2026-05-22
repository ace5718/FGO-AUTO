"""Load and validate Quest profile, navigation, and battle YAML files."""

from __future__ import annotations

from pathlib import Path

import yaml

from fgo_auto.quest.models import BattleScript, NavigationScript, QuestProfile
from fgo_auto.run.run_config import ConfigError


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _data_root() -> Path:
    return _repo_root() / "data"


def resolve_quest_profile_dir(quest_id: str) -> Path:
    for base in (_data_root() / "profiles" / "quests", _repo_root() / "examples" / "quests"):
        candidate = base / quest_id
        if (candidate / "profile.yaml").is_file():
            return candidate
    raise ConfigError(f"Quest profile not found: {quest_id}")


def load_quest_profile(quest_id_or_path: str | Path) -> tuple[QuestProfile, Path]:
    if isinstance(quest_id_or_path, Path):
        profile_dir = quest_id_or_path.resolve()
        profile_path = profile_dir / "profile.yaml"
    else:
        text = str(quest_id_or_path)
        if Path(text).is_file():
            profile_path = Path(text).resolve()
            profile_dir = profile_path.parent
        else:
            profile_dir = resolve_quest_profile_dir(text)
            profile_path = profile_dir / "profile.yaml"

    if not profile_path.is_file():
        raise ConfigError(f"Quest profile missing: {profile_path}")

    data = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    profile = QuestProfile.model_validate(data)
    return profile, profile_dir


def load_navigation_script(path: Path) -> NavigationScript:
    if not path.is_file():
        raise ConfigError(f"Navigation script not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return NavigationScript.model_validate(data)


def load_battle_script(path: Path) -> BattleScript:
    if not path.is_file():
        raise ConfigError(f"Battle script not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return BattleScript.model_validate(data)


def load_quest_bundle(quest_id_or_path: str | Path) -> tuple[QuestProfile, NavigationScript, BattleScript, Path]:
    profile, profile_dir = load_quest_profile(quest_id_or_path)
    nav_path = profile_dir / profile.navigation_script
    battle_path = profile_dir / profile.battle_script
    navigation = load_navigation_script(nav_path)
    battle = load_battle_script(battle_path)
    return profile, navigation, battle, profile_dir
