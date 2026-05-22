from pathlib import Path

import pytest

from fgo_auto.run.run_config import ConfigError, RunConfig, load_run_config


def test_load_valid_yaml(tmp_path: Path) -> None:
    path = tmp_path / "run.yaml"
    path.write_text(
        """
script: test_script
loop_limit: 3
window_title_rule: BlueStacks
anchors:
  enter_quest: a.png
recognition_retries: 5
display_preset: [1920, 1080]
""",
        encoding="utf-8",
    )
    config = load_run_config(path)
    assert config.script == "test_script"
    assert config.loop_limit == 3
    assert config.window_title_rule == "BlueStacks"
    assert config.anchors["enter_quest"] == "a.png"
    assert config.recognition_retries == 5
    assert config.display_preset == (1920, 1080)


def test_missing_field_raises(tmp_path: Path) -> None:
    path = tmp_path / "run.yaml"
    path.write_text("script: only\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_run_config(path)


def test_example_run_config_loads() -> None:
    path = Path(__file__).resolve().parents[1] / "examples" / "run.example.yaml"
    config = load_run_config(path)
    assert isinstance(config, RunConfig)
