from __future__ import annotations

from pathlib import Path

from fgo_auto import __version__


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def data_root() -> Path:
    return repo_root() / "data"


def default_profile_dir() -> Path:
    return data_root() / "profiles" / "default"


def default_run_config_path() -> Path:
    return default_profile_dir() / "run.yaml"


def default_script_config_path() -> Path:
    return default_profile_dir() / "script.yaml"


def logs_dir() -> Path:
    return repo_root() / "logs"


def catalog_dir_for_preset(width: int, height: int) -> Path:
    """Preset-specific catalog under data/catalog/{w}x{h}/, with fallbacks."""
    preset_dir = data_root() / "catalog" / f"{width}x{height}"
    if preset_dir.is_dir():
        return preset_dir
    legacy = repo_root() / "catalog"
    if legacy.is_dir():
        return legacy
    fixture_v02 = repo_root() / "tests" / "fixtures" / "catalog_v02"
    if fixture_v02.is_dir():
        return fixture_v02
    return repo_root() / "tests" / "fixtures" / "catalog"


def catalog_dir() -> Path:
    return catalog_dir_for_preset(1920, 1080)


def ensure_profile_layout(profile_dir: Path | None = None) -> Path:
    root = profile_dir or default_profile_dir()
    root.mkdir(parents=True, exist_ok=True)
    (data_root() / "anchors").mkdir(parents=True, exist_ok=True)
    logs_dir().mkdir(parents=True, exist_ok=True)
    return root


def app_version() -> str:
    return __version__
