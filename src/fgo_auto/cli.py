from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import structlog
import typer

from fgo_auto import __version__
from fgo_auto.host.capture import CaptureError, FixtureHostCapture, create_host_capture
from fgo_auto.host.window_binder import WindowBindingError, create_window_binder
from fgo_auto.logging_setup import configure_logging
from fgo_auto.run.anchor_set import merge_anchor_set
from fgo_auto.run.controller import RunController, RunOutcome
from fgo_auto.run_config import ConfigError, load_run_config, load_script_config
from fgo_auto.script.ap_reader import FakeAPReader, TemplateAPReader
from fgo_auto.script.engine import ScriptEngine
from fgo_auto.vision.image_match import ImageMatch
from fgo_auto.vision.state_catalog import StateCatalog

app = typer.Typer(no_args_is_help=True, help="FGO-AUTO: TW BlueStacks 5 automation CLI")
config_app = typer.Typer(help="Run config utilities")
app.add_typer(config_app, name="config")

logger = structlog.get_logger()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_catalog_dir() -> Path:
    candidate = _repo_root() / "catalog"
    if candidate.is_dir():
        return candidate
    return _repo_root() / "tests" / "fixtures" / "catalog"


def _resolve_config_path(config: Path) -> Path:
    return config.expanduser().resolve()


def _load_merged_config(config_path: Path):
    config = load_run_config(config_path)
    base = config_path.parent
    script_anchors: dict[str, str] = {}
    if config.script_config:
        script_anchors = load_script_config(
            Path(config.script_config) if Path(config.script_config).is_absolute() else base / config.script_config
        )
    anchors = merge_anchor_set(script_anchors, config.anchors, base_dir=base)
    return config, anchors


@app.command("version")
def version_cmd() -> None:
    typer.echo(__version__)


@config_app.command("validate")
def config_validate(
    config_path: Path = typer.Argument(..., help="Path to run.yaml or run.json"),
) -> None:
    """Load and validate a Run config."""
    try:
        run_config = load_run_config(_resolve_config_path(config_path))
        typer.echo(json.dumps(run_config.summary(), indent=2))
    except ConfigError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@app.command("window-pick")
def window_pick(
    title_rule: str = typer.Option(..., "--rule", help="Window title rule"),
) -> None:
    """List matching windows and bind by numeric choice (Window pick)."""
    from fgo_auto.host.window_binder import _matches_rule

    binder = create_window_binder()
    try:
        windows = [w for w in binder.list_windows() if _matches_rule(w.title, title_rule)]
    except Exception as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    if not windows:
        typer.echo(f"No windows matched: {title_rule!r}", err=True)
        raise typer.Exit(1)
    for index, window in enumerate(windows, start=1):
        typer.echo(f"[{index}] handle={window.handle} {window.width}x{window.height} {window.title!r}")
    choice = typer.prompt("Select window number", type=int)
    if choice < 1 or choice > len(windows):
        typer.echo("Invalid selection", err=True)
        raise typer.Exit(1)
    selected = windows[choice - 1]
    typer.echo(json.dumps({"handle": selected.handle, "title": selected.title}))


@app.command("capture-frame")
def capture_frame(
    config_path: Path = typer.Option(..., "--config", "-c", help="Run config path"),
    output: Path = typer.Option(Path("logs/frame.png"), "--output", "-o"),
    pick_handle: Optional[int] = typer.Option(None, "--pick-handle", help="Window handle from window-pick"),
    fixture: Optional[Path] = typer.Option(None, "--fixture", help="Use PNG fixture instead of live capture"),
) -> None:
    """Capture one frame from the bound Host window."""
    configure_logging()
    try:
        config, _ = _load_merged_config(_resolve_config_path(config_path))
        if fixture:
            capture = FixtureHostCapture(fixture, preset=config.display_preset)
        else:
            binder = create_window_binder()
            window = binder.resolve(config.window_title_rule, pick_handle=pick_handle)
            capture = create_host_capture(window, config.display_preset)
        frame = capture.capture()
        output.parent.mkdir(parents=True, exist_ok=True)
        import cv2

        cv2.imwrite(str(output), frame.data)
        typer.echo(f"Saved {output} ({frame.width}x{frame.height})")
    except (ConfigError, WindowBindingError, CaptureError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc


@app.command("detect")
def detect_loop(
    config_path: Path = typer.Option(..., "--config", "-c"),
    catalog_dir: Optional[Path] = typer.Option(None, "--catalog-dir"),
    iterations: int = typer.Option(5, "--iterations", "-n"),
    fixture: Optional[Path] = typer.Option(None, "--fixture"),
    pick_handle: Optional[int] = typer.Option(None, "--pick-handle"),
) -> None:
    """Detect-only loop: log Screen state transitions."""
    configure_logging()
    try:
        config, _ = _load_merged_config(_resolve_config_path(config_path))
        catalog_path = catalog_dir or _default_catalog_dir()
        catalog = StateCatalog.from_directory(catalog_path)
        if fixture:
            capture = FixtureHostCapture(fixture, preset=config.display_preset)
        else:
            binder = create_window_binder()
            window = binder.resolve(config.window_title_rule, pick_handle=pick_handle)
            capture = create_host_capture(window, config.display_preset)
        controller = RunController(
            catalog=catalog,
            capture=capture,
            recognition_retries=config.recognition_retries,
        )
        for i in range(iterations):
            state = controller.detect_screen_state()
            logger.info("screen_state", iteration=i + 1, state=state.value)
            if controller.check_recognition_failure():
                raise typer.Exit(2)
    except (ConfigError, WindowBindingError, CaptureError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc


@app.command("tap-anchor")
def tap_anchor(
    config_path: Path = typer.Option(..., "--config", "-c"),
    name: str = typer.Option(..., "--name", "-n", help="Quest anchor name"),
    fixture: Optional[Path] = typer.Option(None, "--fixture"),
    pick_handle: Optional[int] = typer.Option(None, "--pick-handle"),
) -> None:
    """Find one Quest anchor on the current frame and tap its center."""
    configure_logging()
    try:
        config, anchors = _load_merged_config(_resolve_config_path(config_path))
        if name not in anchors:
            raise ConfigError(f"Anchor not in Anchor set: {name}")
        if fixture:
            capture = FixtureHostCapture(fixture, preset=config.display_preset)
        else:
            binder = create_window_binder()
            window = binder.resolve(config.window_title_rule, pick_handle=pick_handle)
            capture = create_host_capture(window, config.display_preset)
        frame = capture.capture()
        matcher = ImageMatch()
        match = matcher.find(frame, anchors[name])
        if match is None:
            typer.echo(f"No match for anchor {name!r}", err=True)
            raise typer.Exit(1)
        typer.echo(f"match score={match.score:.3f} center={match.center}")
        engine = ScriptEngine(
            controller=RunController(catalog=StateCatalog.from_directory(_default_catalog_dir()), capture=capture, recognition_retries=1),
            capture=capture,
            matcher=matcher,
            ap_reader=FakeAPReader(),
            anchor_paths=anchors,
            loop_limit=config.loop_limit,
        )
        engine._click(match.center)
    except (ConfigError, WindowBindingError, CaptureError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc


@app.command("run")
def run_cmd(
    config_path: Path = typer.Option(..., "--config", "-c"),
    catalog_dir: Optional[Path] = typer.Option(None, "--catalog-dir"),
    fixture: Optional[Path] = typer.Option(None, "--fixture", help="Offline run with PNG sequence directory or single image"),
    pick_handle: Optional[int] = typer.Option(None, "--pick-handle"),
    ap_insufficient_template: Optional[Path] = typer.Option(None, "--ap-insufficient-template"),
    battle_assist_template: Optional[Path] = typer.Option(None, "--battle-assist-template"),
) -> None:
    """Start a Run (Quest loop v0)."""
    configure_logging()
    try:
        config, anchors = _load_merged_config(_resolve_config_path(config_path))
        catalog_path = catalog_dir or _default_catalog_dir()
        catalog = StateCatalog.from_directory(catalog_path)

        if fixture:
            capture = FixtureHostCapture(fixture, preset=config.display_preset)
        else:
            binder = create_window_binder()
            window = binder.resolve(config.window_title_rule, pick_handle=pick_handle)
            capture = create_host_capture(window, config.display_preset)

        controller = RunController(
            catalog=catalog,
            capture=capture,
            recognition_retries=config.recognition_retries,
        )
        ap_reader = TemplateAPReader(ap_insufficient_template) if ap_insufficient_template else FakeAPReader(True)
        engine = ScriptEngine(
            controller=controller,
            capture=capture,
            matcher=ImageMatch(),
            ap_reader=ap_reader,
            anchor_paths=anchors,
            loop_limit=config.loop_limit,
            battle_assist_template=battle_assist_template,
        )

        def _handle_sigint(*_args) -> None:
            engine.request_manual_stop()

        if sys.platform == "win32":
            import signal

            signal.signal(signal.SIGINT, _handle_sigint)

        outcome = engine.run_until_done()
        typer.echo(f"Run finished: {outcome.value} ({controller.status.reason})")
        if outcome is RunOutcome.PAUSED:
            raise typer.Exit(2)
        if outcome is RunOutcome.NORMAL_END:
            raise typer.Exit(0)
    except (ConfigError, WindowBindingError, CaptureError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc


if __name__ == "__main__":
    app()
