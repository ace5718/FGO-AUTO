from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Frame:
    """BGR image array from Host capture."""

    data: np.ndarray

    @property
    def width(self) -> int:
        return int(self.data.shape[1])

    @property
    def height(self) -> int:
        return int(self.data.shape[0])

    def matches_display_preset(self, preset: tuple[int, int]) -> bool:
        return (self.width, self.height) == preset
