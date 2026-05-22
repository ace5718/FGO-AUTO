from pathlib import Path

import cv2
import numpy as np
import pytest

from fgo_auto.run.run_config import ConfigError
from fgo_auto.services.quest_flow_service import copy_profile_to_user, save_quest_anchor_crop


def test_save_quest_anchor_crop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import fgo_auto.quest.loader as ql
    from fgo_auto.services import quest_flow_service as qfs

    repo = Path(__file__).resolve().parents[1]
    data_root = tmp_path / "data"
    monkeypatch.setattr(qfs, "data_root", lambda: data_root)
    monkeypatch.setattr(qfs, "repo_root", lambda: repo)
    monkeypatch.setattr(ql, "_data_root", lambda: data_root)
    monkeypatch.setattr(ql, "_repo_root", lambda: repo)

    frame = np.zeros((100, 200, 3), dtype=np.uint8)
    frame[20:40, 30:70] = (0, 255, 0)
    frame_path = tmp_path / "frame.png"
    cv2.imwrite(str(frame_path), frame)

    copy_profile_to_user("crop_test")
    out = save_quest_anchor_crop("crop_test", "gate", (30, 20, 70, 40), frame_path=frame_path)
    assert out.is_file()
    assert out.name == "gate.png"
    assert out.parent.name == "anchors"


def test_save_quest_anchor_example_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import fgo_auto.quest.loader as ql
    from fgo_auto.services import quest_flow_service as qfs

    repo = Path(__file__).resolve().parents[1]
    data_root = tmp_path / "data"
    monkeypatch.setattr(qfs, "data_root", lambda: data_root)
    monkeypatch.setattr(qfs, "repo_root", lambda: repo)
    monkeypatch.setattr(ql, "_data_root", lambda: data_root)
    monkeypatch.setattr(ql, "_repo_root", lambda: repo)

    frame_path = tmp_path / "frame.png"
    cv2.imwrite(str(frame_path), np.zeros((50, 50, 3), dtype=np.uint8))

    with pytest.raises(ConfigError):
        save_quest_anchor_crop("treasure_door_extreme", "x", (0, 0, 10, 10), frame_path=frame_path)
