from __future__ import annotations

import time
from pathlib import Path

import structlog

from fgo_auto.host.tap import swipe_pixels, tap_pixels
from fgo_auto.quest.loader import resolve_quest_profile_dir
from fgo_auto.quest.models import (
    DelayStep,
    NavigationScript,
    NavigationStep,
    QuestProfile,
    RefreshUntilAnchorStep,
    RunSubflowStep,
    ScrollUntilAnchorStep,
    TapAnchorStep,
    TapCoordinateStep,
    WaitScreenStep,
)
from fgo_auto.services.quest_flow_service import anchor_png_path, load_subflow_script
from fgo_auto.services.paths import data_root
from fgo_auto.vision.image_match import MatchResult
from fgo_auto.run.controller import RunController
from fgo_auto.vision.image_match import ImageMatch
from fgo_auto.vision.screen_state import ScreenState

logger = structlog.get_logger()

SCREEN_ALIASES: dict[str, ScreenState] = {
    "main": ScreenState.MAIN,
    "terminal": ScreenState.TERMINAL,
    "battle": ScreenState.BATTLE,
    "result": ScreenState.RESULT,
}


class NavigationEngine:
    def __init__(
        self,
        controller: RunController,
        matcher: ImageMatch,
        anchor_paths: dict[str, Path],
        *,
        quest_profile: QuestProfile | None = None,
        poll_interval_s: float = 0.3,
    ) -> None:
        self.controller = controller
        self.matcher = matcher
        self.anchor_paths = anchor_paths
        self.quest_profile = quest_profile
        self.poll_interval_s = poll_interval_s
        self._step_index = 0
        self._finished = False

    @property
    def finished(self) -> bool:
        return self._finished

    def reset(self) -> None:
        self._step_index = 0
        self._finished = False

    def run_script(self, navigation: NavigationScript) -> bool:
        """Run all navigation steps. Returns False if paused on failure."""
        self.reset()
        while self._step_index < len(navigation.steps):
            step = navigation.steps[self._step_index]
            ok = self._run_step(step, navigation, anchor_profile_dir=None)
            if not ok:
                return False
            self._step_index += 1
        self._finished = True
        logger.info("navigation_complete", steps=len(navigation.steps))
        return True

    def _run_step(
        self,
        step: NavigationStep,
        navigation: NavigationScript,
        *,
        anchor_profile_dir: Path | None = None,
    ) -> bool:
        if isinstance(step, TapAnchorStep):
            return self._tap_anchor(step.name, anchor_profile_dir=anchor_profile_dir)
        if isinstance(step, TapCoordinateStep):
            return self._tap_coordinate(step)
        if isinstance(step, ScrollUntilAnchorStep):
            return self._scroll_until_anchor(
                step.name, step.max_attempts, anchor_profile_dir=anchor_profile_dir
            )
        if isinstance(step, WaitScreenStep):
            return self._wait_screen(step.state, step.timeout_s)
        if isinstance(step, DelayStep):
            time.sleep(step.seconds)
            logger.info("navigation_step", action="delay", seconds=step.seconds)
            return True
        if isinstance(step, RunSubflowStep):
            return self._run_subflow(step.ref, step.repeat, step.interval_s)
        if isinstance(step, RefreshUntilAnchorStep):
            return self._refresh_until_anchor(
                step.name,
                step.max_attempts,
                refresh_name=step.refresh_anchor,
                anchor_profile_dir=anchor_profile_dir,
            )
        logger.warning("navigation_unknown_step", step=step)
        return True

    def _run_subflow(self, ref: str, repeat: int = 1, interval_s: float = 0.5) -> bool:
        if not self.quest_profile:
            logger.warning("navigation_subflow_missing", ref=ref)
            return True
        profile_dir = resolve_quest_profile_dir(self.quest_profile.quest_id)
        script, anchor_dir = load_subflow_script(profile_dir, self.quest_profile, ref)
        if script is None or not script.steps:
            logger.warning("navigation_subflow_missing", ref=ref)
            return True
        for run in range(1, repeat + 1):
            for sub_step in script.steps:
                if not self._run_step(sub_step, script, anchor_profile_dir=anchor_dir):
                    return False
            if run < repeat:
                time.sleep(interval_s)
        logger.info(
            "navigation_step",
            action="run_subflow",
            ref=ref,
            repeat=repeat,
            interval_s=interval_s,
        )
        return True

    def _refresh_until_anchor(
        self,
        name: str,
        max_attempts: int,
        *,
        refresh_name: str = "friend_refresh",
        anchor_profile_dir: Path | None = None,
    ) -> bool:
        """Tap target when visible; otherwise tap refresh anchor and retry."""
        for attempt in range(1, max_attempts + 1):
            found = self._find_anchor(name, anchor_profile_dir=anchor_profile_dir)
            if found is not None:
                _, match = found
                tap_pixels(match.center)
                logger.info(
                    "navigation_step",
                    action="refresh_until_anchor",
                    anchor=name,
                    attempt=attempt,
                    score=match.score,
                )
                return True
            if attempt < max_attempts:
                if not self._tap_anchor(refresh_name, anchor_profile_dir=anchor_profile_dir):
                    logger.warning(
                        "friend_refresh_missing",
                        anchor=refresh_name,
                        attempt=attempt,
                    )
                    return False
                time.sleep(0.6)
        self.controller._enter_pause(f"Friend support: target not found after refresh: {name}")
        logger.error(
            "friend_support_target_not_found",
            anchor=name,
            max_attempts=max_attempts,
        )
        return False

    def _anchor_path(
        self, name: str, *, anchor_profile_dir: Path | None = None
    ) -> Path | None:
        path = self.anchor_paths.get(name)
        if path is not None and path.is_file():
            return path
        if anchor_profile_dir is not None:
            resolved = anchor_png_path(anchor_profile_dir, name)
            if resolved is not None:
                return resolved
        shared = data_root() / "anchors" / f"{name}.png"
        if shared.is_file():
            return shared
        return None

    def _find_anchor(
        self, name: str, *, anchor_profile_dir: Path | None = None
    ) -> tuple[Path, MatchResult] | None:
        path = self._anchor_path(name, anchor_profile_dir=anchor_profile_dir)
        if path is None:
            return None
        frame = self.controller.capture.capture()
        match = self.matcher.find(frame, path)
        if match is None:
            return None
        return path, match

    def _tap_anchor(self, name: str, *, anchor_profile_dir: Path | None = None) -> bool:
        found = self._find_anchor(name, anchor_profile_dir=anchor_profile_dir)
        if found is None:
            path = self._anchor_path(name, anchor_profile_dir=anchor_profile_dir)
            if path is None:
                self.controller._enter_pause(f"Missing navigation anchor: {name}")
                logger.error("navigation_anchor_missing", anchor=name)
            else:
                self.controller._enter_pause(f"Anchor not found: {name}")
                logger.error("navigation_anchor_not_found", anchor=name)
            return False
        _, match = found
        tap_pixels(match.center)
        logger.info("navigation_step", action="tap_anchor", anchor=name, score=match.score)
        return True

    def _tap_coordinate(self, step: TapCoordinateStep) -> bool:
        tap_pixels((step.x, step.y))
        logger.info(
            "navigation_step",
            action="tap_coordinate",
            x=step.x,
            y=step.y,
        )
        return True

    def _scroll_until_anchor(
        self, name: str, max_attempts: int, *, anchor_profile_dir: Path | None = None
    ) -> bool:
        for attempt in range(1, max_attempts + 1):
            found = self._find_anchor(name, anchor_profile_dir=anchor_profile_dir)
            if found is not None:
                _, match = found
                tap_pixels(match.center)
                logger.info(
                    "navigation_step",
                    action="scroll_until_anchor",
                    anchor=name,
                    attempt=attempt,
                    score=match.score,
                )
                return True
            if attempt < max_attempts:
                self._swipe_quest_list_down()
                time.sleep(0.45)
        self.controller._enter_pause(f"Scroll: anchor not found: {name}")
        logger.error("navigation_scroll_anchor_not_found", anchor=name, max_attempts=max_attempts)
        return False

    def _swipe_quest_list_down(self) -> None:
        """Swipe upward on the list so lower quests scroll into view."""
        frame = self.controller.capture.capture()
        w, h = frame.width, frame.height
        x = int(w * 0.82)
        y_start = int(h * 0.72)
        y_end = int(h * 0.28)
        swipe_pixels((x, y_start), (x, y_end))
        logger.info("navigation_swipe_list", x=x, y_start=y_start, y_end=y_end)

    def _wait_screen(self, state_name: str, timeout_s: float) -> bool:
        target = SCREEN_ALIASES.get(state_name.lower())
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            detected = self.controller.detect_screen_state()
            logger.info(
                "navigation_step",
                action="wait_screen",
                target=state_name,
                detected=detected.value,
            )
            if target is None or detected == target:
                return True
            time.sleep(self.poll_interval_s)
        self.controller._enter_pause(f"wait_screen timeout: {state_name}")
        logger.error("navigation_wait_timeout", state=state_name, timeout_s=timeout_s)
        return False
