from pathlib import Path

import pytest
import yaml

from fgo_auto.services.config_service import ConfigService


@pytest.fixture
def profile_dir(tmp_path: Path) -> Path:
    root = tmp_path / "profiles" / "test"
    root.mkdir(parents=True)
    run_path = root / "run.yaml"
    run_path.write_text(
        yaml.safe_dump(
            {
                "script": "farm",
                "loop_limit": 3,
                "window_title_rule": "BlueStacks",
                "recognition_retries": 2,
                "display_preset": [1920, 1080],
            }
        ),
        encoding="utf-8",
    )
    return root


def test_load_save_validate(profile_dir: Path) -> None:
    svc = ConfigService(profile_dir)
    loaded = svc.load_run()
    assert loaded.loop_limit == 3
    summary = svc.validate_run(loaded)
    assert summary["loop_limit"] == 3
    loaded.loop_limit = 5
    svc.save_run(loaded)
    reloaded = svc.load_run()
    assert reloaded.loop_limit == 5


def test_profile_paths(profile_dir: Path) -> None:
    svc = ConfigService(profile_dir)
    assert svc.profile_dir == profile_dir
    assert svc.run_path.name == "run.yaml"


def test_save_anchor_crop_requires_preview_frame(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fgo_auto.run.run_config import ConfigError
    from fgo_auto.services import config_service as cs

    empty_data = tmp_path / "data"
    monkeypatch.setattr(cs, "data_root", lambda: empty_data)

    svc = ConfigService(tmp_path / "p")
    with pytest.raises(ConfigError):
        svc.save_anchor_crop("x", (0, 0, 10, 10))


def test_list_catalog_states_returns_dirs() -> None:
    svc = ConfigService()
    states = svc.list_catalog_states((1920, 1080))
    assert isinstance(states, list)
