from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from fgo_auto.vision.frame import Frame
from fgo_auto.vision.image_match import ImageMatch
from fgo_auto.vision.screen_state import ScreenState


class StateCatalog:
    """Built-in TW flow Screen state detectors via template bundles."""

    def __init__(
        self,
        templates: dict[ScreenState, list[np.ndarray]],
        threshold: float = 0.75,
    ) -> None:
        self._templates = templates
        self._matcher = ImageMatch(threshold=threshold)

    @classmethod
    def from_directory(cls, catalog_dir: Path, threshold: float = 0.75) -> StateCatalog:
        templates: dict[ScreenState, list[np.ndarray]] = {state: [] for state in ScreenState}
        if catalog_dir.is_dir():
            for state in ScreenState:
                state_dir = catalog_dir / state.value
                if not state_dir.is_dir():
                    continue
                for path in sorted(state_dir.glob("*.png")):
                    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
                    if image is not None:
                        templates[state].append(image)
        return cls(templates=templates, threshold=threshold)

    def detect(self, frame: Frame) -> ScreenState:
        best_state = ScreenState.UNKNOWN
        best_score = 0.0

        for state, refs in self._templates.items():
            if state is ScreenState.UNKNOWN:
                continue
            for ref in refs:
                match = self._matcher.find_in_frame(frame, ref)
                if match and match.score > best_score:
                    best_score = match.score
                    best_state = state

        if best_state is ScreenState.UNKNOWN or best_score < self._matcher.threshold:
            return ScreenState.UNKNOWN
        return best_state
