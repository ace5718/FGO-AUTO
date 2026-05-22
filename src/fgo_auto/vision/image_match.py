from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from fgo_auto.vision.frame import Frame


@dataclass(frozen=True)
class MatchResult:
    x: int
    y: int
    score: float
    template_width: int
    template_height: int

    @property
    def center(self) -> tuple[int, int]:
        return (self.x + self.template_width // 2, self.y + self.template_height // 2)


class ImageMatch:
    def __init__(self, threshold: float = 0.8) -> None:
        self.threshold = threshold

    def find(self, frame: Frame, template_path: Path) -> MatchResult | None:
        if not template_path.is_file():
            raise FileNotFoundError(f"Template not found: {template_path}")

        template = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
        if template is None:
            raise ValueError(f"Could not read template image: {template_path}")

        result = cv2.matchTemplate(frame.data, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val < self.threshold:
            return None

        h, w = template.shape[:2]
        return MatchResult(
            x=int(max_loc[0]),
            y=int(max_loc[1]),
            score=float(max_val),
            template_width=w,
            template_height=h,
        )

    def find_in_frame(self, frame: Frame, template_bgr: np.ndarray) -> MatchResult | None:
        result = cv2.matchTemplate(frame.data, template_bgr, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val < self.threshold:
            return None
        h, w = template_bgr.shape[:2]
        return MatchResult(
            x=int(max_loc[0]),
            y=int(max_loc[1]),
            score=float(max_val),
            template_width=w,
            template_height=h,
        )
