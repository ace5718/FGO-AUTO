from pathlib import Path
from unittest.mock import MagicMock

import cv2
import numpy as np
import pytest

from fgo_auto.host.capture import FixtureHostCapture
from fgo_auto.quest.models import NavigationScript, ScrollUntilAnchorStep
from fgo_auto.run.controller import RunController
from fgo_auto.script.navigation import NavigationEngine
from fgo_auto.vision.image_match import ImageMatch
from fgo_auto.vision.state_catalog import StateCatalog


def _write_green_patch(path: Path, size: int = 40) -> None:
    patch = np.full((size, size, 3), (0, 255, 0), dtype=np.uint8)
    cv2.imwrite(str(path), patch)


def _frame_with_patch(src: Path, dest: Path, patch_src: Path) -> None:
    frame = cv2.imread(str(src))
    patch = cv2.imread(str(patch_src))
    ph, pw = patch.shape[:2]
    frame[40 : 40 + ph, 60 : 60 + pw] = patch
    cv2.imwrite(str(dest), frame)


def test_scroll_until_anchor_finds_without_swipe(
    fixtures_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    anchor_path = tmp_path / "scroll_target.png"
    _write_green_patch(anchor_path)
    frame_path = tmp_path / "terminal_patched.png"
    _frame_with_patch(fixtures_dir / "frames" / "terminal.png", frame_path, anchor_path)

    capture = FixtureHostCapture(frame_path)
    catalog = StateCatalog.from_directory(fixtures_dir / "catalog")
    controller = RunController(catalog=catalog, capture=capture, recognition_retries=3)
    engine = NavigationEngine(controller, ImageMatch(threshold=0.5), {"scroll_target": anchor_path})

    swipe = MagicMock()
    monkeypatch.setattr("fgo_auto.script.navigation.swipe_pixels", swipe)
    monkeypatch.setattr("fgo_auto.script.navigation.tap_pixels", MagicMock())

    navigation = NavigationScript(
        steps=[ScrollUntilAnchorStep(name="scroll_target", max_attempts=3)]
    )
    assert engine.run_script(navigation)
    swipe.assert_not_called()
