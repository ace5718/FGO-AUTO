from pathlib import Path
from unittest.mock import MagicMock

import cv2
import numpy as np
import pytest

from fgo_auto.host.capture import FixtureHostCapture
from fgo_auto.quest.models import FriendSupportConfig, QuestProfile
from fgo_auto.run.controller import RunController
from fgo_auto.script.navigation import NavigationEngine
from fgo_auto.services.paths import catalog_dir_for_preset
from fgo_auto.vision.image_match import ImageMatch, MatchResult
from fgo_auto.vision.state_catalog import StateCatalog


def test_refresh_until_anchor_finds_on_second_attempt(tmp_path: Path) -> None:
    target = tmp_path / "friend_target.png"
    refresh = tmp_path / "friend_refresh.png"
    patch = np.full((20, 20, 3), (0, 255, 0), dtype=np.uint8)
    cv2.imwrite(str(target), patch)
    cv2.imwrite(str(refresh), patch)
    frame_path = tmp_path / "blank.png"
    cv2.imwrite(str(frame_path), np.zeros((200, 200, 3), dtype=np.uint8))

    capture = FixtureHostCapture(frame_path)
    catalog = StateCatalog.from_directory(catalog_dir_for_preset(1920, 1080))
    controller = RunController(catalog=catalog, capture=capture, recognition_retries=3)

    profile = QuestProfile(
        quest_id="t",
        navigation_script="navigation.yaml",
        battle_script="battle.yaml",
        friend_support=FriendSupportConfig(
            max_refresh_attempts=3,
            steps=[{"action": "refresh_until_anchor", "name": "friend_target"}],
        ),
    )

    engine = NavigationEngine(
        controller,
        ImageMatch(threshold=0.5),
        {"friend_target": target, "friend_refresh": refresh},
        quest_profile=profile,
        poll_interval_s=0,
    )

    calls = {"n": 0}

    def fake_find(frame_obj, path: Path) -> MatchResult | None:
        calls["n"] += 1
        if path == target and calls["n"] >= 2:
            return MatchResult(x=40, y=40, score=0.9, template_width=20, template_height=20)
        return None

    engine.matcher.find = fake_find  # type: ignore[method-assign]
    engine._tap_anchor = MagicMock(return_value=True)  # type: ignore[method-assign]

    import fgo_auto.script.navigation as nav_mod

    tapped: list[tuple[int, int]] = []
    nav_mod.tap_pixels = lambda pt: tapped.append(pt)

    ok = engine._refresh_until_anchor("friend_target", 3)
    assert ok is True
    assert tapped == [(50, 50)]
    assert engine._tap_anchor.call_count == 1
