from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fgo_auto.run_config import RunConfig


@dataclass
class AppState:
    profile_dir: Path
    run_config: RunConfig | None = None
    pick_handle: int | None = None
    bound_window_title: str = ""
    run_active: bool = False
    last_screen_state: str = ""
    loops_completed: int = 0
    last_capture_path: Path | None = None
    status_message: str = ""
