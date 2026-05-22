from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

import structlog

from fgo_auto.host.capture import HostCapture
from fgo_auto.quest.models import BattleScript, NavigationScript, QuestProfile
from fgo_auto.run.controller import RunController, RunOutcome
from fgo_auto.script.ap_reader import APReader, FakeAPReader
from fgo_auto.script.battle_script import BattleScriptEngine
from fgo_auto.script.navigation import NavigationEngine
from fgo_auto.vision.image_match import ImageMatch
from fgo_auto.vision.screen_state import ScreenState

logger = structlog.get_logger()


class ScriptPhaseV2(Enum):
    DETECT = auto()
    NAVIGATE = auto()
    DEPLOY = auto()
    BATTLE = auto()
    WAIT_RESULT = auto()
    AFTER_RESULT = auto()
    END = auto()


@dataclass
class ScriptEngineV2:
    controller: RunController
    capture: HostCapture
    matcher: ImageMatch
    navigation: NavigationScript
    battle: BattleScript
    quest_profile: QuestProfile
    anchor_paths: dict[str, Path]
    loop_limit: int = 0
    ap_reader: APReader = field(default_factory=lambda: FakeAPReader(True))
    poll_interval_s: float = 1.0
    manual_stop: bool = False
    loops_completed: int = 0
    phase: ScriptPhaseV2 = ScriptPhaseV2.DETECT
    navigation_engine: NavigationEngine | None = None
    battle_engine: BattleScriptEngine | None = None
    navigation_done: bool = False
    battle_done: bool = False

    def __post_init__(self) -> None:
        self.navigation_engine = NavigationEngine(
            self.controller,
            self.matcher,
            self.anchor_paths,
            quest_profile=self.quest_profile,
            poll_interval_s=0.3,
        )
        self.battle_engine = BattleScriptEngine(self.controller)

    def request_manual_stop(self) -> None:
        self.manual_stop = True

    def tick(self) -> RunOutcome:
        if self.manual_stop:
            self.controller.end_normal("Manual stop")
            self.phase = ScriptPhaseV2.END
            return RunOutcome.NORMAL_END

        if self.controller.status.outcome is RunOutcome.PAUSED:
            return RunOutcome.PAUSED

        if self.loop_limit > 0 and self.loops_completed >= self.loop_limit:
            self.controller.end_normal("Loop limit reached")
            self.phase = ScriptPhaseV2.END
            return RunOutcome.NORMAL_END

        state = self.controller.detect_screen_state()
        if self.controller.check_recognition_failure():
            self.phase = ScriptPhaseV2.END
            return RunOutcome.PAUSED

        if self.phase is ScriptPhaseV2.DETECT:
            self._handle_detect(state)
        elif self.phase is ScriptPhaseV2.NAVIGATE:
            self._handle_navigate()
        elif self.phase is ScriptPhaseV2.DEPLOY:
            self._handle_deploy(state)
        elif self.phase is ScriptPhaseV2.BATTLE:
            self._handle_battle(state)
        elif self.phase is ScriptPhaseV2.WAIT_RESULT:
            self._handle_wait_result(state)
        elif self.phase is ScriptPhaseV2.AFTER_RESULT:
            self._handle_after_result(state)
        elif self.phase is ScriptPhaseV2.END:
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
            self.phase = ScriptPhaseV2.NAVIGATE
            self.navigation_done = False
            self.battle_done = False
        elif state is ScreenState.MAIN:
            logger.info("script_v2_at_main", hint="Navigate from Terminal for Quest loop")
        elif state is ScreenState.BATTLE:
            self.phase = ScriptPhaseV2.BATTLE
        elif state is ScreenState.RESULT:
            self.phase = ScriptPhaseV2.AFTER_RESULT

    def _handle_navigate(self) -> None:
        if self.navigation_done:
            self.phase = ScriptPhaseV2.DEPLOY
            return
        assert self.navigation_engine is not None
        ok = self.navigation_engine.run_script(self.navigation)
        if not ok:
            self.phase = ScriptPhaseV2.END
            return
        self.navigation_done = True
        self.phase = ScriptPhaseV2.DEPLOY

    def _handle_deploy(self, state: ScreenState) -> None:
        if not self.ap_reader.has_sufficient_ap(self.capture.capture()):
            self.controller.end_normal("AP insufficient")
            self.phase = ScriptPhaseV2.END
            return
        logger.info("deploy_ready", hint="Confirm sortie in UI if needed")
        self.phase = ScriptPhaseV2.BATTLE

    def _handle_battle(self, state: ScreenState) -> None:
        if self.battle_done:
            self.phase = ScriptPhaseV2.WAIT_RESULT
            return
        if state is not ScreenState.BATTLE and state is not ScreenState.UNKNOWN:
            self.phase = ScriptPhaseV2.WAIT_RESULT
            return
        assert self.battle_engine is not None
        ok = self.battle_engine.run(self.battle)
        if not ok:
            self.phase = ScriptPhaseV2.END
            return
        self.battle_done = True
        self.phase = ScriptPhaseV2.WAIT_RESULT

    def _handle_wait_result(self, state: ScreenState) -> None:
        if state is ScreenState.RESULT:
            self.phase = ScriptPhaseV2.AFTER_RESULT

    def _handle_after_result(self, state: ScreenState) -> None:
        if state is ScreenState.TERMINAL:
            self.loops_completed += 1
            self.controller.status.loops_completed = self.loops_completed
            logger.info("quest_loop_iteration_done", count=self.loops_completed)
            self.navigation_done = False
            self.battle_done = False
            if self.navigation_engine:
                self.navigation_engine.reset()
            if self.battle_engine:
                self.battle_engine.reset()
            self.phase = ScriptPhaseV2.NAVIGATE
        elif state is ScreenState.MAIN:
            self.phase = ScriptPhaseV2.DETECT


def create_script_engine_v2(
    controller: RunController,
    quest_id: str,
    anchor_paths: dict[str, Path],
    *,
    loop_limit: int = 0,
    ap_reader: APReader | None = None,
    poll_interval_s: float = 1.0,
) -> ScriptEngineV2:
    from fgo_auto.quest.loader import load_quest_bundle

    profile, navigation, battle, _profile_dir = load_quest_bundle(quest_id)
    return ScriptEngineV2(
        controller=controller,
        capture=controller.capture,
        matcher=ImageMatch(),
        navigation=navigation,
        battle=battle,
        quest_profile=profile,
        anchor_paths=anchor_paths,
        loop_limit=loop_limit,
        ap_reader=ap_reader or FakeAPReader(True),
        poll_interval_s=poll_interval_s,
    )
