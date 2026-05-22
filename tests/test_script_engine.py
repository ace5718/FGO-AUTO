from pathlib import Path

from fgo_auto.host.capture import FixtureHostCapture
from fgo_auto.run.controller import RunController, RunOutcome
from fgo_auto.script.ap_reader import FakeAPReader
from fgo_auto.script.engine import ScriptEngine, ScriptPhase
from fgo_auto.vision.image_match import ImageMatch
from fgo_auto.vision.state_catalog import StateCatalog


def test_loop_limit_ends_normally(fixtures_dir: Path) -> None:
    frame = fixtures_dir / "frames" / "terminal.png"
    capture = FixtureHostCapture(frame)
    catalog = StateCatalog.from_directory(fixtures_dir / "catalog")
    controller = RunController(catalog=catalog, capture=capture, recognition_retries=5)
    anchors = {"enter_quest": fixtures_dir / "anchors" / "enter_quest.png"}
    engine = ScriptEngine(
        controller=controller,
        capture=capture,
        matcher=ImageMatch(threshold=0.7),
        ap_reader=FakeAPReader(True),
        anchor_paths=anchors,
        loop_limit=0,
        poll_interval_s=0,
    )
    engine.phase = ScriptPhase.DETECT
    outcome = engine.tick()
    assert outcome is RunOutcome.NORMAL_END


def test_ap_insufficient_ends_run(fixtures_dir: Path) -> None:
    frame = fixtures_dir / "frames" / "terminal.png"
    capture = FixtureHostCapture(frame)
    catalog = StateCatalog.from_directory(fixtures_dir / "catalog")
    controller = RunController(catalog=catalog, capture=capture, recognition_retries=5)
    anchors = {"enter_quest": fixtures_dir / "anchors" / "enter_quest.png"}
    engine = ScriptEngine(
        controller=controller,
        capture=capture,
        matcher=ImageMatch(threshold=0.7),
        ap_reader=FakeAPReader(False),
        anchor_paths=anchors,
        loop_limit=10,
        poll_interval_s=0,
    )
    engine.phase = ScriptPhase.DEPLOY
    outcome = engine.tick()
    assert outcome is RunOutcome.NORMAL_END
    assert "AP" in controller.status.reason
