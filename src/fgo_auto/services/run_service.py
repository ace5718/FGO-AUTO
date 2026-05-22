from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from fgo_auto.run.controller import RunController, RunOutcome
from fgo_auto.script.ap_reader import APReader, FakeAPReader
from fgo_auto.script.engine import ScriptEngine
from fgo_auto.script.engine_v2 import ScriptEngineV2
from fgo_auto.services.paths import catalog_dir
from fgo_auto.vision.image_match import ImageMatch
from fgo_auto.vision.screen_state import ScreenState
from fgo_auto.vision.state_catalog import StateCatalog


class RunEventType(str, Enum):
    SCREEN_STATE = "screen_state"
    OUTCOME = "outcome"
    ERROR = "error"


@dataclass(frozen=True)
class RunEvent:
    type: RunEventType
    message: str
    screen_state: ScreenState | None = None
    outcome: RunOutcome | None = None
    loops_completed: int = 0


ScriptEngineLike = ScriptEngine | ScriptEngineV2


class RunService:
    def __init__(self, engine: ScriptEngineLike) -> None:
        self._engine = engine
        self._events: queue.Queue[RunEvent] = queue.Queue()
        self._thread: threading.Thread | None = None

    @property
    def engine(self) -> ScriptEngineLike:
        return self._engine

    @property
    def events(self) -> queue.Queue[RunEvent]:
        return self._events

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.is_running():
            raise RuntimeError("Run already in progress")
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._engine.request_manual_stop()

    def _emit(self, event: RunEvent) -> None:
        self._events.put(event)

    def _run_loop(self) -> None:
        try:
            for _ in range(10_000):
                outcome = self._engine.tick()
                state = self._engine.controller.status.last_screen_state
                loops = self._engine.controller.status.loops_completed
                self._emit(
                    RunEvent(
                        RunEventType.SCREEN_STATE,
                        state.value,
                        screen_state=state,
                        loops_completed=loops,
                    )
                )
                if outcome is not RunOutcome.RUNNING:
                    reason = self._engine.controller.status.reason
                    self._emit(
                        RunEvent(
                            RunEventType.OUTCOME,
                            f"{outcome.value}: {reason}",
                            outcome=outcome,
                            loops_completed=loops,
                        )
                    )
                    break
                time.sleep(self._engine.poll_interval_s)
            else:
                self._engine.controller.end_normal("Max ticks exceeded")
                self._emit(
                    RunEvent(
                        RunEventType.OUTCOME,
                        RunOutcome.NORMAL_END.value,
                        outcome=RunOutcome.NORMAL_END,
                        loops_completed=self._engine.controller.status.loops_completed,
                    )
                )
        except Exception as exc:
            self._emit(RunEvent(RunEventType.ERROR, str(exc)))
        finally:
            self._thread = None


def build_script_engine(
    controller: RunController,
    anchor_paths: dict[str, Path],
    loop_limit: int,
    battle_assist_template: Path | None = None,
    ap_reader: APReader | None = None,
    poll_interval_s: float = 1.0,
) -> ScriptEngine:
    return ScriptEngine(
        controller=controller,
        capture=controller.capture,
        matcher=ImageMatch(),
        ap_reader=ap_reader or FakeAPReader(True),
        anchor_paths=anchor_paths,
        loop_limit=loop_limit,
        battle_assist_template=battle_assist_template,
        poll_interval_s=poll_interval_s,
    )


def default_catalog() -> StateCatalog:
    return StateCatalog.from_directory(catalog_dir())
