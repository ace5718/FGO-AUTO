"""Backward-compatible import path for Run configuration.

Prefer: ``from fgo_auto.run.run_config import RunConfig``
"""

from fgo_auto.run.run_config import (
    ConfigError,
    RunConfig,
    load_run_config,
    load_script_config,
)

__all__ = [
    "ConfigError",
    "RunConfig",
    "load_run_config",
    "load_script_config",
]
