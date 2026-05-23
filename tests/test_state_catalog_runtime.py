import numpy as np

from fgo_auto.vision.frame import Frame
from fgo_auto.vision.screen_state import ScreenState
from fgo_auto.vision.state_catalog import StateCatalog


def test_runtime_session_registers_main() -> None:
    image = np.zeros((1080, 1920, 3), dtype=np.uint8)
    image[100:200, 100:200] = (255, 0, 0)
    frame = Frame(data=image)
    catalog = StateCatalog.from_runtime_session(frame)
    assert catalog.learns_at_runtime
    assert catalog.detect(frame) is ScreenState.MAIN


def test_runtime_register_learns_new_state() -> None:
    main_img = np.zeros((1080, 1920, 3), dtype=np.uint8)
    main_img[50:150, 50:150] = (255, 0, 0)
    catalog = StateCatalog.from_runtime_session(Frame(data=main_img))
    battle_img = np.zeros((1080, 1920, 3), dtype=np.uint8)
    battle_img[300:400, 300:400] = (0, 255, 0)
    battle_frame = Frame(data=battle_img)
    catalog.register(battle_frame, ScreenState.BATTLE)
    assert catalog.detect(battle_frame) is ScreenState.BATTLE
