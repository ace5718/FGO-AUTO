from pathlib import Path

import pytest

from fgo_auto.quest.models import RunSubflowStep, ScrollUntilAnchorStep, TapAnchorStep
from fgo_auto.run.run_config import ConfigError
from fgo_auto.quest.models import FriendSupportConfig, QuestProfile
from fgo_auto.services.quest_flow_service import (
    copy_profile_to_user,
    create_blank_profile,
    delete_quest_anchor,
    delete_user_quest_profile,
    dict_to_step,
    friend_support_anchor_names,
    friend_support_anchor_plain,
    list_example_quest_profiles,
    list_quest_profiles,
    list_user_quest_profiles,
    subflow_picker_options,
    list_saved_anchors,
    load_flow,
    navigation_uses_friend_support,
    save_navigation,
    save_profile,
    step_to_dict,
)


def test_list_quest_profiles_includes_example() -> None:
    ids = {e.quest_id for e in list_quest_profiles()}
    assert "treasure_door_extreme" in ids


def test_subflow_picker_lists_other_user_schemes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import fgo_auto.quest.loader as ql
    from fgo_auto.services import quest_flow_service as qfs

    repo = Path(__file__).resolve().parents[1]
    data_root = tmp_path / "data"
    monkeypatch.setattr(qfs, "data_root", lambda: data_root)
    monkeypatch.setattr(qfs, "repo_root", lambda: repo)
    monkeypatch.setattr(ql, "_data_root", lambda: data_root)
    monkeypatch.setattr(ql, "_repo_root", lambda: repo)

    copy_profile_to_user("main_scheme")
    copy_profile_to_user("helper_scheme")
    opts = subflow_picker_options("main_scheme")
    refs = {o.ref for o in opts}
    assert "helper_scheme" in refs
    assert "main_scheme" not in refs


def test_list_user_excludes_examples(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import fgo_auto.quest.loader as ql
    from fgo_auto.services import quest_flow_service as qfs

    repo = Path(__file__).resolve().parents[1]
    data_root = tmp_path / "data"
    monkeypatch.setattr(qfs, "data_root", lambda: data_root)
    monkeypatch.setattr(qfs, "repo_root", lambda: repo)
    monkeypatch.setattr(ql, "_data_root", lambda: data_root)
    monkeypatch.setattr(ql, "_repo_root", lambda: repo)

    assert any(e.quest_id == "treasure_door_extreme" for e in list_example_quest_profiles())
    create_blank_profile("only_user")
    users = list_user_quest_profiles()
    assert all(e.is_user_copy for e in users)
    assert "treasure_door_extreme" not in {e.quest_id for e in users}


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
    profile, navigation, profile_dir = load_flow("blank_quest")
    assert profile.display_name == "測試關卡"
    assert any(isinstance(s, RunSubflowStep) for s in navigation.steps)
    assert (profile_dir / "subflows" / "friend_support.yaml").is_file()


def test_friend_support_anchor_plain_known() -> None:
    assert "職階" in friend_support_anchor_plain("friend_class_all")
    assert "更新" in friend_support_anchor_plain("friend_refresh")


def test_friend_support_anchor_names_defaults() -> None:
    profile = QuestProfile(
        quest_id="x",
        navigation_script="navigation.yaml",
        battle_script="battle.yaml",
    )
    assert friend_support_anchor_names(profile) == [
        "friend_class_all",
        "friend_target",
        "friend_refresh",
    ]


def test_load_subflow_friend_support_script(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import fgo_auto.quest.loader as ql
    from fgo_auto.services import quest_flow_service as qfs

    repo = Path(__file__).resolve().parents[1]
    data_root = tmp_path / "data"
    monkeypatch.setattr(qfs, "data_root", lambda: data_root)
    monkeypatch.setattr(qfs, "repo_root", lambda: repo)
    monkeypatch.setattr(ql, "_data_root", lambda: data_root)
    monkeypatch.setattr(ql, "_repo_root", lambda: repo)

    create_blank_profile("sf_quest")
    profile, _, profile_dir = load_flow("sf_quest")
    script, anchor_dir = qfs.load_subflow_script(profile_dir, profile, "friend_support")
    assert script is not None
    assert anchor_dir == profile_dir
    assert len(script.steps) >= 2


def test_load_subflow_by_other_quest_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import fgo_auto.quest.loader as ql
    from fgo_auto.services import quest_flow_service as qfs

    repo = Path(__file__).resolve().parents[1]
    data_root = tmp_path / "data"
    monkeypatch.setattr(qfs, "data_root", lambda: data_root)
    monkeypatch.setattr(qfs, "repo_root", lambda: repo)
    monkeypatch.setattr(ql, "_data_root", lambda: data_root)
    monkeypatch.setattr(ql, "_repo_root", lambda: repo)

    copy_profile_to_user("scheme_a")
    copy_profile_to_user("scheme_b")
    profile_a, _, dir_a = load_flow("scheme_a")
    script, anchor_dir = qfs.load_subflow_script(dir_a, profile_a, "scheme_b")
    assert script is not None
    assert anchor_dir is not None
    assert anchor_dir.name == "scheme_b"


def test_navigation_uses_friend_support() -> None:
    from fgo_auto.quest.models import NavigationScript, RunSubflowStep

    nav = NavigationScript(steps=[RunSubflowStep(ref="friend_support")])
    assert navigation_uses_friend_support(nav) is True


def test_friend_support_anchor_names_includes_refresh_button() -> None:
    profile = QuestProfile(
        quest_id="x",
        navigation_script="navigation.yaml",
        battle_script="battle.yaml",
        friend_support=FriendSupportConfig(
            steps=[
                {"tap": "friend_class_all"},
                {"action": "refresh_until_anchor", "name": "friend_target"},
            ],
        ),
    )
    names = friend_support_anchor_names(profile)
    assert "friend_refresh" in names
    assert "friend_target" in names


def test_friend_support_anchor_names_from_profile() -> None:
    profile = QuestProfile(
        quest_id="x",
        navigation_script="navigation.yaml",
        battle_script="battle.yaml",
        friend_support=FriendSupportConfig(
            steps=[{"tap": "a"}, {"tap": "b"}],
        ),
    )
    assert friend_support_anchor_names(profile) == ["a", "b"]


def test_delete_quest_anchor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import fgo_auto.quest.loader as ql
    from fgo_auto.services import quest_flow_service as qfs

    repo = Path(__file__).resolve().parents[1]
    data_root = tmp_path / "data"
    monkeypatch.setattr(qfs, "data_root", lambda: data_root)
    monkeypatch.setattr(qfs, "repo_root", lambda: repo)
    monkeypatch.setattr(ql, "_data_root", lambda: data_root)
    monkeypatch.setattr(ql, "_repo_root", lambda: repo)

    dest = create_blank_profile("del_anchor")
    png = dest / "anchors" / "test_btn.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n")
    assert "test_btn" in list_saved_anchors(dest)
    delete_quest_anchor("test_btn", profile_dir=dest)
    assert list_saved_anchors(dest) == []


def test_delete_user_quest_profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import fgo_auto.quest.loader as ql
    from fgo_auto.services import quest_flow_service as qfs

    repo = Path(__file__).resolve().parents[1]
    data_root = tmp_path / "data"
    monkeypatch.setattr(qfs, "data_root", lambda: data_root)
    monkeypatch.setattr(qfs, "repo_root", lambda: repo)
    monkeypatch.setattr(ql, "_data_root", lambda: data_root)
    monkeypatch.setattr(ql, "_repo_root", lambda: repo)

    create_blank_profile("to_delete")
    assert (data_root / "profiles" / "quests" / "to_delete").is_dir()
    delete_user_quest_profile("to_delete")
    assert not (data_root / "profiles" / "quests" / "to_delete").exists()


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
