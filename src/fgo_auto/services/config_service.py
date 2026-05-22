from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

import yaml

from fgo_auto.run.anchor_set import merge_anchor_set
from fgo_auto.run_config import ConfigError, RunConfig, load_run_config, load_script_config
from fgo_auto.services.paths import ensure_profile_layout, repo_root


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

    def save_anchor_crop(self, name: str, _rect: tuple[int, int, int, int]) -> Path:
        raise NotImplementedError("Phase 2: anchor crop from preview")

    def list_catalog_states(self) -> list[str]:
        raise NotImplementedError("Phase 2: catalog manager")
