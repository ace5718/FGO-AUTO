from pathlib import Path

import pytest

from fgo_auto.quest.models import ScrollUntilAnchorStep, TapAnchorStep
from fgo_auto.run.run_config import ConfigError
from fgo_auto.services.quest_flow_service import (
    copy_profile_to_user,
    create_blank_profile,
    dict_to_step,
    list_quest_profiles,
    load_flow,
    save_navigation,
    step_to_dict,
)


def test_list_quest_profiles_includes_example() -> None:
    ids = {e.quest_id for e in list_quest_profiles()}
    assert "treasure_door_extreme" in ids


def test_step_roundtrip_dict() -> None:
    step = TapAnchorStep(name="chaldea_gate")
    restored = dict_to_step(step_to_dict(step))
    assert restored.name == "chaldea_gate"


def test_scroll_until_anchor_roundtrip() -> None:
    step = ScrollUntilAnchorStep(name="daily_quests", max_attempts=5)
    restored = dict_to_step(step_to_dict(step))
    assert isinstance(restored, ScrollUntilAnchorStep)
    assert restored.name == "daily_quests"
    assert restored.max_attempts == 5


def test_copy_and_save_flow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import fgo_auto.quest.loader as ql
    from fgo_auto.services import quest_flow_service as qfs

    repo = Path(__file__).resolve().parents[1]
    data_root = tmp_path / "data"
    monkeypatch.setattr(qfs, "data_root", lambda: data_root)
    monkeypatch.setattr(qfs, "repo_root", lambda: repo)
    monkeypatch.setattr(ql, "_data_root", lambda: data_root)
    monkeypatch.setattr(ql, "_repo_root", lambda: repo)

    dest = copy_profile_to_user("test_custom_quest")
    assert dest.is_dir()
    profile, navigation, profile_dir = load_flow("test_custom_quest")
    navigation.steps.append(TapAnchorStep(name="extra_step"))
    path = save_navigation(profile_dir, navigation)
    assert path.is_file()
    reloaded = load_flow("test_custom_quest")[1]
    assert any(isinstance(s, TapAnchorStep) and s.name == "extra_step" for s in reloaded.steps)


def test_create_blank_profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import fgo_auto.quest.loader as ql
    from fgo_auto.services import quest_flow_service as qfs

    repo = Path(__file__).resolve().parents[1]
    data_root = tmp_path / "data"
    monkeypatch.setattr(qfs, "data_root", lambda: data_root)
    monkeypatch.setattr(qfs, "repo_root", lambda: repo)
    monkeypatch.setattr(ql, "_data_root", lambda: data_root)
    monkeypatch.setattr(ql, "_repo_root", lambda: repo)

    dest = create_blank_profile("blank_quest", "測試關卡")
    assert dest.is_dir()
    profile, navigation, _ = load_flow("blank_quest")
    assert profile.display_name == "測試關卡"
    assert navigation.steps == []


def test_copy_duplicate_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import fgo_auto.quest.loader as ql
    from fgo_auto.services import quest_flow_service as qfs

    repo = Path(__file__).resolve().parents[1]
    data_root = tmp_path / "data"
    monkeypatch.setattr(qfs, "data_root", lambda: data_root)
    monkeypatch.setattr(qfs, "repo_root", lambda: repo)
    monkeypatch.setattr(ql, "_data_root", lambda: data_root)
    monkeypatch.setattr(ql, "_repo_root", lambda: repo)
    copy_profile_to_user("dup_quest")
    with pytest.raises(ConfigError):
        copy_profile_to_user("dup_quest")
