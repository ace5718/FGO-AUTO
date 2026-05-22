from pathlib import Path

from typer.testing import CliRunner

from fgo_auto.cli import app


def test_version() -> None:
    result = CliRunner().invoke(app, ["version"])
    assert result.exit_code == 0
    from fgo_auto import __version__

    assert __version__ in result.stdout


def test_config_validate_example() -> None:
    config = Path(__file__).resolve().parents[1] / "examples" / "run.example.yaml"
    result = CliRunner().invoke(app, ["config", "validate", str(config)])
    assert result.exit_code == 0
    assert "farm_default" in result.stdout


def test_config_validate_invalid(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("script: only\n", encoding="utf-8")
    result = CliRunner().invoke(app, ["config", "validate", str(bad)])
    assert result.exit_code == 1
