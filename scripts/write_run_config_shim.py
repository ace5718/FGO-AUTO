from pathlib import Path

CONTENT = '''"""Backward-compatible import path for Run configuration.

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
'''

def main() -> None:
    path = Path(__file__).resolve().parents[1] / "src" / "fgo_auto" / "run_config.py"
    path.write_text(CONTENT, encoding="utf-8", newline="\n")
    assert b"\x00" not in path.read_bytes()
    print("wrote", path)


if __name__ == "__main__":
    main()
