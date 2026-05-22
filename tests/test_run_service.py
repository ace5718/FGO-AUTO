from pathlib import Path

import pytest

from fgo_auto.host.capture import FixtureHostCapture
from fgo_auto.run.controller import RunController, RunOutcome
from fgo_auto.script.ap_reader import FakeAPReader
from fgo_auto.services.run_service import RunEventType, RunService, build_script_engine
from fgo_auto.vision.state_catalog import StateCatalog


@pytest.fixture
def engine_stack(fixtures_dir: Path):
    catalog = StateCatalog.from_directory(fixtures_dir / "catalog")
    capture = FixtureHostCapture(fixtures_dir / "frames" / "terminal.png", preset=(1920, 1080))
    controller = RunController(catalog=catalog, capture=capture, recognition_retries=5)
    anchors = {"enter_quest": fixtures_dir / "anchors" / "enter_quest.png"}
    engine = build_script_engine(
        controller,
        anchors,
        loop_limit=1,
        ap_reader=FakeAPReader(True),
        poll_interval_s=0.01,
    )
    return engine


def test_run_service_manual_stop(engine_stack) -> None:
    import queue

    engine = engine_stack
    svc = RunService(engine)
    svc.start()
    svc.stop()
    outcome = None
    deadline = 5.0
    import time

    start = time.monotonic()
    while time.monotonic() - start < deadline:
        try:
            event = svc.events.get(timeout=0.2)
        except queue.Empty:
            if not svc.is_running():
                break
            continue
        if event.type is RunEventType.OUTCOME:
            outcome = event.outcome
            break
    assert outcome in (RunOutcome.NORMAL_END, RunOutcome.PAUSED)
