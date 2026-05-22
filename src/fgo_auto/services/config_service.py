from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

import yaml

from fgo_auto.run.anchor_set import merge_anchor_set
from fgo_auto.run.run_config import ConfigError, RunConfig, load_run_config, load_script_config
from fgo_auto.services.paths import (
    catalog_dir_for_preset,
    data_root,
    ensure_profile_layout,
    repo_root,
)


@dataclass(frozen=True)
class MergedRunContext:
    config: RunConfig
    config_path: Path
    anchors: dict[str, Path]


class ConfigService:
    def __init__(self, profile_dir: Path | None = None) -> None:
        self.profile_dir = ensure_profile_layout(profile_dir)
        self.run_path = self.profile_dir / "run.yaml"
        self.script_path = self.profile_dir / "script.yaml"

    def list_profiles(self) -> list[str]:
        profiles_root = repo_root() / "data" / "profiles"
        if not profiles_root.is_dir():
            return ["default"]
        names = sorted(p.name for p in profiles_root.iterdir() if p.is_dir())
        return names or ["default"]

    def load_run(self, path: Path | None = None) -> RunConfig:
        target = path or self.run_path
        if not target.is_file():
            raise ConfigError(f"Run config not found: {target}")
        return load_run_config(target)

    def save_run(self, config: RunConfig, path: Path | None = None) -> Path:
        target = path or self.run_path
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = config.model_dump(mode="json")
        target.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return target

    def validate_run(self, config: RunConfig) -> dict:
        return config.summary()

    def load_merged(self, run_path: Path | None = None) -> MergedRunContext:
        run_path = (run_path or self.run_path).resolve()
        config = self.load_run(run_path)
        base = run_path.parent
        script_anchors: dict[str, str] = {}
        script_file = config.script_config
        if script_file:
            script_path = Path(script_file) if Path(script_file).is_absolute() else base / script_file
            script_anchors = load_script_config(script_path)
        elif self.script_path.is_file():
            script_anchors = load_script_config(self.script_path)
        anchors = merge_anchor_set(script_anchors, config.anchors, base_dir=base)
        return MergedRunContext(config=config, config_path=run_path, anchors=anchors)

    def seed_default_profile(self) -> None:
        """Copy example profile into data/profiles/default if missing."""
        if self.run_path.is_file():
            return
        example_run = repo_root() / "examples" / "data-profile" / "run.yaml"
        example_script = repo_root() / "examples" / "data-profile" / "script.yaml"
        if example_run.is_file():
            shutil.copy2(example_run, self.run_path)
        if example_script.is_file():
            shutil.copy2(example_script, self.script_path)

    def save_anchor_crop(self, name: str, rect: tuple[int, int, int, int]) -> Path:
        """Save anchor PNG under data/anchors/ and register in script.yaml."""
        import cv2

        anchors_dir = data_root() / "anchors"
        anchors_dir.mkdir(parents=True, exist_ok=True)
        frame_path = anchors_dir / "_last_frame_preview.png"
        if not frame_path.is_file():
            raise ConfigError("No preview frame saved; capture a frame before cropping anchor")
        frame = cv2.imread(str(frame_path))
        if frame is None:
            raise ConfigError(f"Could not read frame: {frame_path}")
        x1, y1, x2, y2 = rect
        crop = frame[y1:y2, x1:x2]
        out = anchors_dir / f"{name}.png"
        cv2.imwrite(str(out), crop)
        script_data: dict = {}
        if self.script_path.is_file():
            script_data = yaml.safe_load(self.script_path.read_text(encoding="utf-8")) or {}
        anchors_map = script_data.setdefault("anchors", {})
        if not isinstance(anchors_map, dict):
            raise ConfigError("script.yaml anchors must be a mapping")
        anchors_map[name] = f"../../anchors/{name}.png"
        self.script_path.write_text(
            yaml.safe_dump(script_data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return out

    def save_preview_frame(self, frame_path: Path) -> None:
        """Store last captured frame for anchor crop (GUI preview)."""
        import shutil

        anchors_dir = data_root() / "anchors"
        anchors_dir.mkdir(parents=True, exist_ok=True)
        for p in anchors_dir.glob("_last_frame_*.png"):
            p.unlink(missing_ok=True)
        shutil.copy2(frame_path, anchors_dir / "_last_frame_preview.png")

    def list_catalog_states(self, preset: tuple[int, int] = (1920, 1080)) -> list[str]:
        root = catalog_dir_for_preset(preset[0], preset[1])
        if not root.is_dir():
            return []
        return sorted(
            p.name
            for p in root.iterdir()
            if p.is_dir() and not p.name.startswith(".")
        )
