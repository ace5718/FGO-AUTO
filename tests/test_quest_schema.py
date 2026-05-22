import pytest

from fgo_auto.quest.loader import ConfigError, load_quest_bundle


def test_load_treasure_door_extreme_profile() -> None:
    profile, navigation, battle, profile_dir = load_quest_bundle("treasure_door_extreme")
    assert profile.quest_id == "treasure_door_extreme"
    assert profile_dir.name == "treasure_door_extreme"
    assert len(navigation.steps) >= 5
    assert len(battle.turns) == 2
    assert battle.turns[0].actions[0].type == "servant_skill"


def test_quest_profile_missing_raises() -> None:
    with pytest.raises(ConfigError):
        load_quest_bundle("nonexistent_quest_xyz")
