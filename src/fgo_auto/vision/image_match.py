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
    scale: float = 1.0

    @property
    def center(self) -> tuple[int, int]:
        return (self.x + self.template_width // 2, self.y + self.template_height // 2)


def _scale_steps(scale_min: float, scale_max: float, steps: int) -> list[float]:
    if steps < 2 or scale_min >= scale_max:
        return [1.0]
    return [float(s) for s in np.linspace(scale_min, scale_max, steps)]


@dataclass
class ImageMatch:
    """Template match with optional multi-scale search for resolution / UI scale drift."""

    threshold: float = 0.8
    scale_min: float = 0.85
    scale_max: float = 1.15
    scale_steps: int = 9

    def find(self, frame: Frame, template_path: Path) -> MatchResult | None:
        if not template_path.is_file():
            raise FileNotFoundError(f"Template not found: {template_path}")

        template = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
        if template is None:
            raise ValueError(f"Could not read template image: {template_path}")

        return self._best_match(frame, template)

    def find_in_frame(self, frame: Frame, template_bgr: np.ndarray) -> MatchResult | None:
        return self._best_match(frame, template_bgr)

    def _best_match(self, frame: Frame, template: np.ndarray) -> MatchResult | None:
        best: MatchResult | None = None
        th0, tw0 = template.shape[:2]

        for scale in _scale_steps(self.scale_min, self.scale_max, self.scale_steps):
            if abs(scale - 1.0) < 1e-6:
                scaled = template
                tw, th = tw0, th0
            else:
                tw = max(8, int(round(tw0 * scale)))
                th = max(8, int(round(th0 * scale)))
                if tw > frame.width or th > frame.height:
                    continue
                scaled = cv2.resize(template, (tw, th), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)

            result = cv2.matchTemplate(frame.data, scaled, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            score = float(max_val)
            if score < self.threshold:
                continue
            candidate = MatchResult(
                x=int(max_loc[0]),
                y=int(max_loc[1]),
                score=score,
                template_width=tw,
                template_height=th,
                scale=scale,
            )
            if best is None or candidate.score > best.score:
                best = candidate

        return best
