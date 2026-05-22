from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from fgo_auto.vision.screen_state import ScreenState

FIXTURES = Path(__file__).parent / "fixtures"


def _write_catalog_fixtures() -> None:
    catalog = FIXTURES / "catalog"
    placements = {
        ScreenState.MAIN: ((80, 80), (40, 80, 200)),
        ScreenState.TERMINAL: ((500, 400), (0, 255, 255)),
        ScreenState.BATTLE: ((900, 200), (200, 80, 40)),
        ScreenState.RESULT: ((1200, 700), (200, 40, 200)),
    }
    base = np.zeros((1080, 1920, 3), dtype=np.uint8)
    for state, ((x, y), color) in placements.items():
        state_dir = catalog / state.value
        state_dir.mkdir(parents=True, exist_ok=True)
        patch = base.copy()
        cv2.rectangle(patch, (x, y), (x + 120, y + 120), color, -1)
        cv2.imwrite(str(state_dir / "ref.png"), patch)
        cv2.imwrite(str(FIXTURES / "frames" / f"{state.value}.png"), patch)


def _write_anchor_fixtures() -> None:
    anchors_dir = FIXTURES / "anchors"
    frames_dir = FIXTURES / "frames"
    anchors_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    cv2.rectangle(frame, (500, 400), (620, 520), (0, 255, 255), -1)
    cv2.imwrite(str(frames_dir / "terminal.png"), frame)
    template = frame[400:520, 500:620].copy()
    cv2.imwrite(str(anchors_dir / "enter_quest.png"), template)
    blank = np.zeros((1080, 1920, 3), dtype=np.uint8)
    cv2.imwrite(str(frames_dir / "blank.png"), blank)


@pytest.fixture(scope="session", autouse=True)
def _ensure_fixtures() -> None:
    marker = FIXTURES / "catalog" / "terminal" / "ref.png"
    if not marker.exists():
        _write_catalog_fixtures()
        _write_anchor_fixtures()


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES
