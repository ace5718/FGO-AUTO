from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import structlog

from fgo_auto.host.capture import HostCapture
from fgo_auto.vision.frame import Frame
from fgo_auto.vision.screen_state import ScreenState
from fgo_auto.vision.state_catalog import StateCatalog

logger = structlog.get_logger()


class RunOutcome(str, Enum):
    RUNNING = "running"
    NORMAL_END = "normal_end"
    PAUSED = "paused"


@dataclass
class RunStatus:
    outcome: RunOutcome
    reason: str = ""
    loops_completed: int = 0
    last_screen_state: ScreenState = ScreenState.UNKNOWN
    recognition_failures: int = 0


@dataclass
class RunController:
    catalog: StateCatalog
    capture: HostCapture
    recognition_retries: int
    log_dir: Path = field(default_factory=lambda: Path("logs"))
    consecutive_unknown: int = 0
    status: RunStatus = field(default_factory=lambda: RunStatus(outcome=RunOutcome.RUNNING))

    def detect_screen_state(self) -> ScreenState:
        frame = self.capture.capture()
        state = self.catalog.detect(frame)
        if state is not ScreenState.UNKNOWN and self.catalog.learns_at_runtime:
            self.catalog.register(frame, state)
        self.status.last_screen_state = state
        if state is ScreenState.UNKNOWN:
            self.consecutive_unknown += 1
            logger.warning(
                "screen_state_unknown",
                failures=self.consecutive_unknown,
                budget=self.recognition_retries,
            )
        else:
            self.consecutive_unknown = 0
        return state

    def check_recognition_failure(self) -> bool:
        if self.consecutive_unknown >= self.recognition_retries:
            self._enter_pause("Recognition failure: retry budget exhausted")
            return True
        return False

    def _enter_pause(self, reason: str) -> None:
        path = self.log_dir / "pause_screenshot.png"
        try:
            self.capture.save_diagnostic(path)
            logger.error("run_pause", reason=reason, screenshot=str(path))
        except Exception as exc:
            logger.error("run_pause", reason=reason, screenshot_error=str(exc))
        self.status.outcome = RunOutcome.PAUSED
        self.status.reason = reason

    def end_normal(self, reason: str) -> None:
        self.status.outcome = RunOutcome.NORMAL_END
        self.status.reason = reason
        logger.info("normal_run_end", reason=reason, loops=self.status.loops_completed)

    def save_frame(self, frame: Frame, name: str) -> Path:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        path = self.log_dir / name
        import cv2

        cv2.imwrite(str(path), frame.data)
        return path
