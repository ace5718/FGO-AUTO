"""Screen-state catalog templates under data/catalog/{w}x{h}/."""

from __future__ import annotations

import shutil
from pathlib import Path

from fgo_auto.services.paths import catalog_dir_for_preset, data_root
from fgo_auto.vision.screen_state import ScreenState


def catalog_preset_dir(width: int, height: int) -> Path:
    return data_root() / "catalog" / f"{width}x{height}"


def count_templates(preset: tuple[int, int]) -> int:
    root = catalog_dir_for_preset(preset[0], preset[1])
    if not root.is_dir():
        return 0
    total = 0
    for state in ScreenState:
        if state is ScreenState.UNKNOWN:
            continue
        state_dir = root / state.value
        if state_dir.is_dir():
            total += len(list(state_dir.glob("*.png")))
    return total


def save_state_template(
    preset: tuple[int, int],
    state: str,
    source_image: Path,
    *,
    filename: str = "seed.png",
) -> Path:
    """Copy a captured PNG into data/catalog/<preset>/<state>/."""
    dest_dir = catalog_preset_dir(preset[0], preset[1]) / state
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename
    shutil.copy2(source_image, dest)
    return dest
