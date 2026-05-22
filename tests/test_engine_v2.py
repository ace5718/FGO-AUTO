from pathlib import Path

from fgo_auto.host.capture import FixtureHostCapture
from fgo_auto.run.controller import RunController, RunOutcome
from fgo_auto.script.engine_v2 import create_script_engine_v2
from fgo_auto.services.paths import catalog_dir_for_preset
from fgo_auto.vision.state_catalog import StateCatalog


def test_script_engine_v2_fixture_ticks(fixtures_dir: Path) -> None:
    frame = fixtures_dir / "frames" / "terminal.png"
    capture = FixtureHostCapture(frame)
    catalog = StateCatalog.from_directory(catalog_dir_for_preset(1920, 1080))
    controller = RunController(catalog=catalog, capture=capture, recognition_retries=5)
    anchors = {"enter_quest": fixtures_dir / "anchors" / "enter_quest.png"}
    engine = create_script_engine_v2(
        controller,
        "treasure_door_extreme",
        anchors,
        loop_limit=0,
    )
    engine.poll_interval_s = 0
    outcome = engine.run_until_done(max_ticks=5)
    assert outcome in {RunOutcome.RUNNING, RunOutcome.PAUSED, RunOutcome.NORMAL_END}
