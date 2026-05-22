from pathlib import Path
import cv2
import numpy as np
from fgo_auto.vision.frame import Frame
from fgo_auto.vision.image_match import ImageMatch

def _patch() -> np.ndarray:
    p = np.zeros((120, 120, 3), dtype=np.uint8)
    cv2.rectangle(p, (8, 8), (112, 112), (0, 255, 255), 2)
    cv2.circle(p, (60, 60), 28, (255, 0, 0), -1)
    return p

def test_find_anchor_on_synthetic_frame(tmp_path: Path) -> None:
    frame_data = np.zeros((1080, 1920, 3), dtype=np.uint8)
    patch = _patch()
    frame_data[400:520, 500:620] = patch
    frame = Frame(data=frame_data)
    anchor_path = tmp_path / "enter_quest.png"
    cv2.imwrite(str(anchor_path), patch)
    match = ImageMatch(threshold=0.7).find(frame, anchor_path)
    assert match is not None
    assert match.x == 500
    assert match.y == 400

def test_no_match_on_blank_frame(tmp_path: Path) -> None:
    frame = Frame(data=np.zeros((1080, 1920, 3), dtype=np.uint8))
    anchor_path = tmp_path / "enter_quest.png"
    cv2.imwrite(str(anchor_path), _patch())
    match = ImageMatch(threshold=0.95).find(frame, anchor_path)
    assert match is None
