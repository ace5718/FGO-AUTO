from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

import structlog

from fgo_auto.host.capture import HostCapture
from fgo_auto.run.controller import RunController, RunOutcome
from fgo_auto.script.ap_reader import APReader
from fgo_auto.vision.image_match import ImageMatch
from fgo_auto.vision.screen_state import ScreenState

logger = structlog.get_logger()


class ScriptPhase(Enum):
    DETECT = auto()
    ENTER_QUEST = auto()
    DEPLOY = auto()
    BATTLE = auto()
    WAIT_RESULT = auto()
    AFTER_RESULT = auto()
    END = auto()


@dataclass
class ScriptEngine:
    controller: RunController
    capture: HostCapture
    matcher: ImageMatch
    ap_reader: APReader
    anchor_paths: dict[str, Path]
    loop_limit: int
    battle_assist_template: Path | None = None
    enter_quest_anchor: str = "enter_quest"
    poll_interval_s: float = 1.0
    phase: ScriptPhase = ScriptPhase.DETECT
    manual_stop: bool = False
    loops_completed: int = field(default=0, init=False)

    def request_manual_stop(self) -> None:
        self.manual_stop = True

    def tick(self) -> RunOutcome:
        if self.manual_stop:
            self.controller.end_normal("Manual stop")
            self.phase = ScriptPhase.END
            return RunOutcome.NORMAL_END

        if self.controller.status.outcome is RunOutcome.PAUSED:
            return RunOutcome.PAUSED

        if self.loops_completed >= self.loop_limit:
            self.controller.end_normal("Loop limit reached")
            self.phase = ScriptPhase.END
            return RunOutcome.NORMAL_END

        state = self.controller.detect_screen_state()
        if self.controller.check_recognition_failure():
            self.phase = ScriptPhase.END
            return RunOutcome.PAUSED

        if self.phase is ScriptPhase.DETECT:
            self._handle_detect(state)
        elif self.phase is ScriptPhase.ENTER_QUEST:
            self._enter_quest()
        elif self.phase is ScriptPhase.DEPLOY:
            self._deploy()
        elif self.phase is ScriptPhase.BATTLE:
            self._battle_assist()
        elif self.phase is ScriptPhase.WAIT_RESULT:
            self._wait_result(state)
        elif self.phase is ScriptPhase.AFTER_RESULT:
            self._after_result(state)
        elif self.phase is ScriptPhase.END:
            return self.controller.status.outcome

        return self.controller.status.outcome

    def run_until_done(self, max_ticks: int = 10_000) -> RunOutcome:
        for _ in range(max_ticks):
            outcome = self.tick()
            if outcome is not RunOutcome.RUNNING:
                return outcome
            time.sleep(self.poll_interval_s)
        self.controller.end_normal("Max ticks exceeded")
        return RunOutcome.NORMAL_END

    def _handle_detect(self, state: ScreenState) -> None:
        if state is ScreenState.TERMINAL:
            self.phase = ScriptPhase.ENTER_QUEST
        elif state is ScreenState.MAIN:
            logger.info("script_at_main", hint="Navigate to Terminal for Quest loop")
        elif state is ScreenState.BATTLE:
            self.phase = ScriptPhase.BATTLE
        elif state is ScreenState.RESULT:
            self.phase = ScriptPhase.AFTER_RESULT

    def _enter_quest(self) -> None:
        path = self.anchor_paths.get(self.enter_quest_anchor)
        if path is None:
            self.controller._enter_pause(f"Missing Quest anchor: {self.enter_quest_anchor}")
            self.phase = ScriptPhase.END
            return
        frame = self.capture.capture()
        match = self.matcher.find(frame, path)
        if match is None:
            logger.warning("quest_anchor_no_match", anchor=self.enter_quest_anchor)
            return
        self._click(match.center)
        logger.info("quest_anchor_tapped", anchor=self.enter_quest_anchor, score=match.score)
        self.phase = ScriptPhase.DEPLOY

    def _deploy(self) -> None:
        frame = self.capture.capture()
        if not self.ap_reader.has_sufficient_ap(frame):
            self.controller.end_normal("AP insufficient")
            self.phase = ScriptPhase.END
            return
        logger.info("deploy_ready", hint="Confirm sortie in UI if needed")
        self.phase = ScriptPhase.BATTLE

    def _battle_assist(self) -> None:
        if self.battle_assist_template and self.battle_assist_template.is_file():
            frame = self.capture.capture()
            match = self.matcher.find(frame, self.battle_assist_template)
            if match:
                self._click(match.center)
                logger.info("battle_assist_tapped", score=match.score)
            else:
                logger.warning("battle_assist_not_found")
        else:
            logger.info("battle_assist_skipped", reason="no template configured")
        self.phase = ScriptPhase.WAIT_RESULT

    def _wait_result(self, state: ScreenState) -> None:
        if state is ScreenState.RESULT:
            self.phase = ScriptPhase.AFTER_RESULT

    def _after_result(self, state: ScreenState) -> None:
        if state is ScreenState.TERMINAL:
            self.loops_completed += 1
            self.controller.status.loops_completed = self.loops_completed
            logger.info("quest_loop_iteration_done", count=self.loops_completed)
            self.phase = ScriptPhase.ENTER_QUEST
        elif state is ScreenState.MAIN:
            self.phase = ScriptPhase.DETECT

    def _click(self, coords: tuple[int, int]) -> None:
        from fgo_auto.host.tap import tap_pixels

        tap_pixels(coords)
