from pathlib import Path

import cv2
import numpy as np

from fgo_auto.host.capture import FixtureHostCapture
from fgo_auto.run.controller import RunController, RunOutcome
from fgo_auto.vision.state_catalog import StateCatalog


def test_recognition_failure_enters_pause(fixtures_dir: Path) -> None:
    blank = fixtures_dir / "frames" / "blank.png"
    image = np.zeros((1080, 1920, 3), dtype=np.uint8)
    cv2.imwrite(str(blank), image)
    catalog = StateCatalog.from_directory(fixtures_dir / "catalog")
    capture = FixtureHostCapture(blank)
    controller = RunController(catalog=catalog, capture=capture, recognition_retries=2, log_dir=fixtures_dir / "logs")
    for _ in range(2):
        controller.detect_screen_state()
    assert controller.check_recognition_failure()
    assert controller.status.outcome is RunOutcome.PAUSED
