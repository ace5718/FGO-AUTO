from pathlib import Path

import cv2
import numpy as np

from fgo_auto.host.capture import FixtureHostCapture
from fgo_auto.quest.models import NavigationScript, TapAnchorStep
from fgo_auto.run.controller import RunController
from fgo_auto.script.navigation import NavigationEngine
from fgo_auto.vision.image_match import ImageMatch
from fgo_auto.vision.state_catalog import StateCatalog


def _terminal_with_green_center(src: Path, dest: Path) -> None:
    frame = cv2.imread(str(src))
    h, w = frame.shape[:2]
    cy, cx = h // 2, w // 2
    frame[cy - 20 : cy + 20, cx - 20 : cx + 20] = (0, 255, 0)
    cv2.imwrite(str(dest), frame)


def _write_green_anchor(path: Path, size: int = 40) -> None:
    patch = np.full((size, size, 3), (0, 255, 0), dtype=np.uint8)
    cv2.imwrite(str(path), patch)


def _engine_for_anchor_tap(
    frame_path: Path,
    catalog_dir: Path,
    anchor_path: Path,
    anchor_name: str = "chaldea_gate",
) -> NavigationEngine:
    capture = FixtureHostCapture(frame_path)
    catalog = StateCatalog.from_directory(catalog_dir)
    controller = RunController(catalog=catalog, capture=capture, recognition_retries=3)
    return NavigationEngine(
        controller,
        ImageMatch(threshold=0.5),
        {anchor_name: anchor_path},
    )


def test_navigation_tap_anchor_step(fixtures_dir: Path, tmp_path: Path) -> None:
    patched = tmp_path / "patched_terminal.png"
    anchor_path = tmp_path / "chaldea_gate.png"
    _terminal_with_green_center(fixtures_dir / "frames" / "terminal.png", patched)
    _write_green_anchor(anchor_path)

    engine = _engine_for_anchor_tap(
        patched,
        fixtures_dir / "catalog",
        anchor_path,
    )
    navigation = NavigationScript(steps=[TapAnchorStep(name="chaldea_gate")])

    assert engine.run_script(navigation)
    assert engine.finished
