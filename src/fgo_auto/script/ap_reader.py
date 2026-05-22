from __future__ import annotations

from pathlib import Path
from typing import Protocol

from fgo_auto.vision.frame import Frame
from fgo_auto.vision.image_match import ImageMatch


class APReader(Protocol):
    def has_sufficient_ap(self, frame: Frame) -> bool: ...


class FakeAPReader:
    def __init__(self, sufficient: bool = True) -> None:
        self._sufficient = sufficient

    def has_sufficient_ap(self, frame: Frame) -> bool:
        return self._sufficient


class TemplateAPReader:
    """Detect insufficient AP when a template (e.g. grayed sortie) matches."""

    def __init__(self, insufficient_template: Path | None, threshold: float = 0.8) -> None:
        self._template = insufficient_template
        self._matcher = ImageMatch(threshold=threshold)

    def has_sufficient_ap(self, frame: Frame) -> bool:
        if self._template is None or not self._template.is_file():
            return True
        match = self._matcher.find(frame, self._template)
        return match is None
