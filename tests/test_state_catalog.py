from pathlib import Path

import cv2

from fgo_auto.vision.frame import Frame
from fgo_auto.vision.screen_state import ScreenState
from fgo_auto.vision.state_catalog import StateCatalog


def test_detect_terminal(fixtures_dir: Path) -> None:
    catalog = StateCatalog.from_directory(fixtures_dir / "catalog")
    image = cv2.imread(str(fixtures_dir / "frames" / "terminal.png"))
    state = catalog.detect(Frame(data=image))
    assert state is ScreenState.TERMINAL


def test_unknown_on_blank() -> None:
    import numpy as np

    catalog = StateCatalog.from_directory(Path("/nonexistent"))
    blank = Frame(data=np.zeros((1080, 1920, 3), dtype=np.uint8))
    assert catalog.detect(blank) is ScreenState.UNKNOWN
