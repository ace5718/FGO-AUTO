from pathlib import Path

import numpy as np
import pytest

from fgo_auto.quest.models import ForRepeatStep, IfAnchorStep, TapAnchorStep
from fgo_auto.run.controller import RunController
from fgo_auto.script.navigation import NavigationEngine, NavigationScript
from fgo_auto.vision.frame import Frame
from fgo_auto.vision.image_match import ImageMatch
from fgo_auto.vision.state_catalog import StateCatalog


@pytest.fixture
def nav_engine(tmp_path: Path) -> NavigationEngine:
    catalog = StateCatalog.from_directory(tmp_path)
    capture = type(
        "Cap",
        (),
        {
            "capture": lambda self: Frame(data=np.zeros((100, 100, 3), dtype=np.uint8)),
            "save_diagnostic": lambda self, p: None,
        },
    )()
    controller = RunController(catalog=catalog, capture=capture, recognition_retries=3)
    return NavigationEngine(controller, ImageMatch(threshold=0.5), {})


def test_if_anchor_runs_then_branch(nav_engine: NavigationEngine, monkeypatch) -> None:
    calls: list[str] = []

    def fake_find(name, **kwargs):
        return (Path("a.png"), type("M", (), {"center": (1, 2), "score": 0.9})())

    def fake_tap(name, **kwargs):
        calls.append(name)
        return True

    monkeypatch.setattr(nav_engine, "_find_anchor", fake_find)
    monkeypatch.setattr(nav_engine, "_tap_anchor", fake_tap)

    script = NavigationScript(
        steps=[
            IfAnchorStep(
                name="gate",
                then_steps=[TapAnchorStep(name="then_tap")],
                else_steps=[TapAnchorStep(name="else_tap")],
            )
        ]
    )
    assert nav_engine.run_script(script) is True
    assert calls == ["then_tap"]


def test_for_repeat_runs_nested_count(nav_engine: NavigationEngine, monkeypatch) -> None:
    taps: list[str] = []

    def fake_tap(name, **kwargs):
        taps.append(name)
        return True

    monkeypatch.setattr(nav_engine, "_tap_anchor", fake_tap)

    script = NavigationScript(
        steps=[
            ForRepeatStep(
                count=3,
                steps=[TapAnchorStep(name="loop_tap")],
            )
        ]
    )
    assert nav_engine.run_script(script) is True
    assert taps == ["loop_tap", "loop_tap", "loop_tap"]
