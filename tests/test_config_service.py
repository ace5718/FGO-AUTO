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


def test_phase2_stubs_raise(tmp_path: Path) -> None:
    svc = ConfigService(tmp_path / "p")
    with pytest.raises(NotImplementedError):
        svc.save_anchor_crop("x", (0, 0, 10, 10))
    with pytest.raises(NotImplementedError):
        svc.list_catalog_states()
