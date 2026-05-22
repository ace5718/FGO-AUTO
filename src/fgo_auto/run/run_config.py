"""Load and validate operator Run configuration (run.yaml / run.json)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator


class ConfigError(Exception):
    """Run config could not be loaded or validated."""


class RunConfig(BaseModel):
    """Operator Run settings: window binding, loop limit, display preset, script version."""

    script: str
    loop_limit: int = Field(default=10, ge=0)
    window_title_rule: str
    anchors: dict[str, str] = Field(default_factory=dict)
    recognition_retries: int = Field(default=5, ge=1)
    display_preset: tuple[int, int] = (1920, 1080)
    script_config: str | None = None
    script_version: Literal["v0", "v2"] = "v0"
    quest_profile: str | None = None

    @field_validator("display_preset", mode="before")
    @classmethod
    def _coerce_display_preset(cls, value: Any) -> tuple[int, int]:
        if value is None:
            return (1920, 1080)
        if isinstance(value, (list, tuple)) and len(value) == 2:
            return (int(value[0]), int(value[1]))
        raise ValueError("display_preset must be [width, height]")

    def summary(self) -> dict[str, Any]:
        return {
            "script": self.script,
            "loop_limit": self.loop_limit,
            "window_title_rule": self.window_title_rule,
            "anchor_names": sorted(self.anchors.keys()),
            "recognition_retries": self.recognition_retries,
            "display_preset": list(self.display_preset),
            "script_config": self.script_config,
            "script_version": self.script_version,
            "quest_profile": self.quest_profile,
        }


def load_run_config(path: Path) -> RunConfig:
    if not path.is_file():
        raise ConfigError(f"Run config not found: {path}")

    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    try:
        if suffix in {".yaml", ".yml"}:
            data = yaml.safe_load(text)
        elif suffix == ".json":
            data = json.loads(text)
        else:
            raise ConfigError(f"Unsupported config format: {suffix} (use .yaml or .json)")
    except (yaml.YAMLError, json.JSONDecodeError) as exc:
        raise ConfigError(f"Invalid config syntax in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError("Run config root must be a mapping")

    try:
        return RunConfig.model_validate(data)
    except Exception as exc:
        raise ConfigError(f"Run config validation failed: {exc}") from exc


def load_script_config(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise ConfigError(f"Script config not found: {path}")
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ConfigError("script config root must be a mapping")
    anchors = data.get("anchors")
    if anchors is None:
        return {}
    if not isinstance(anchors, dict):
        raise ConfigError("script config 'anchors' must be a mapping")
    return {str(k): str(v) for k, v in anchors.items()}
