from __future__ import annotations

import time

import structlog

from fgo_auto.host.tap import tap_normalized
from fgo_auto.quest.models import (
    BattleAction,
    BattleScript,
    CraftSkillAction,
    NoblePhantasmAction,
    SelectCardsAction,
    ServantSkillAction,
)
from fgo_auto.run.controller import RunController

logger = structlog.get_logger()

# Normalized tap targets for TW 1920×1080-class layouts (calibrate per preset).
DEFAULT_POSITIONS: dict[str, tuple[float, float]] = {
    "servant_1_skill_1": (0.12, 0.88),
    "servant_1_skill_2": (0.16, 0.88),
    "servant_1_skill_3": (0.20, 0.88),
    "servant_2_skill_1": (0.32, 0.88),
    "servant_2_skill_2": (0.36, 0.88),
    "servant_2_skill_3": (0.40, 0.88),
    "servant_3_skill_1": (0.52, 0.88),
    "servant_3_skill_2": (0.56, 0.88),
    "servant_3_skill_3": (0.60, 0.88),
    "craft_skill_1": (0.08, 0.75),
    "craft_skill_2": (0.08, 0.70),
    "craft_skill_3": (0.08, 0.65),
    "card_1": (0.35, 0.55),
    "card_2": (0.50, 0.55),
    "card_3": (0.65, 0.55),
    "noble_1": (0.25, 0.92),
    "noble_2": (0.50, 0.92),
    "noble_3": (0.75, 0.92),
}


class BattleScriptEngine:
    def __init__(
        self,
        controller: RunController,
        *,
        positions: dict[str, tuple[float, float]] | None = None,
        action_delay_s: float = 0.4,
        turn_delay_s: float = 0.8,
    ) -> None:
        self.controller = controller
        self.positions = {**DEFAULT_POSITIONS, **(positions or {})}
        self.action_delay_s = action_delay_s
        self.turn_delay_s = turn_delay_s
        self._turn_index = 0
        self._finished = False

    @property
    def finished(self) -> bool:
        return self._finished

    def reset(self) -> None:
        self._turn_index = 0
        self._finished = False

    def run(self, battle: BattleScript) -> bool:
        self.reset()
        turns = battle.turns
        for turn in turns:
            for action in turn.actions:
                if not self._run_action(action):
                    return False
                time.sleep(self.action_delay_s)
            self._turn_index += 1
            logger.info("battle_turn_done", turn=self._turn_index)
            time.sleep(self.turn_delay_s)
        self._finished = True
        logger.info("battle_script_complete", turns=len(turns))
        return True

    def _tap_key(self, key: str) -> bool:
        pos = self.positions.get(key)
        if pos is None:
            self.controller._enter_pause(f"Missing battle position: {key}")
            return False
        frame = self.controller.capture.capture()
        tap_normalized(pos[0], pos[1], frame.width, frame.height)
        return True

    def _run_action(self, action: BattleAction) -> bool:
        if isinstance(action, ServantSkillAction):
            key = f"servant_{action.slot}_skill_{action.skill}"
            logger.info("battle_action", type="servant_skill", key=key)
            return self._tap_key(key)
        if isinstance(action, CraftSkillAction):
            key = f"craft_skill_{action.skill}"
            logger.info("battle_action", type="craft_skill", key=key)
            return self._tap_key(key)
        if isinstance(action, SelectCardsAction):
            for card in action.cards:
                key = f"card_{card}"
                logger.info("battle_action", type="select_cards", card=card)
                if not self._tap_key(key):
                    return False
                time.sleep(self.action_delay_s * 0.5)
            return True
        if isinstance(action, NoblePhantasmAction):
            key = f"noble_{action.slot}"
            logger.info("battle_action", type="noble_phantasm", key=key)
            return self._tap_key(key)
        return True
