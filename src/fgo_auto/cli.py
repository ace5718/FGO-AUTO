from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import structlog
import typer

from fgo_auto import __version__
from fgo_auto.host.capture import CaptureError
from fgo_auto.host.window_binder import WindowBindingError
from fgo_auto.logging_setup import configure_logging
from fgo_auto.run.controller import RunOutcome
from fgo_auto.run.run_config import ConfigError
from fgo_auto.run.controller import RunController
from fgo_auto.script.ap_reader import FakeAPReader
from fgo_auto.script.engine import ScriptEngine
from fgo_auto.services.run_setup import create_capture
from fgo_auto.services.capture_service import CaptureService
from fgo_auto.services.config_service import ConfigService
from fgo_auto.services.paths import catalog_dir, default_run_config_path, logs_dir
from fgo_auto.services.run_setup import create_run_stack, load_context
from fgo_auto.services.window_service import WindowService
from fgo_auto.vision.image_match import ImageMatch
from fgo_auto.vision.state_catalog import StateCatalog

app = typer.Typer(no_args_is_help=True, help="FGO-AUTO: TW BlueStacks 5 automation CLI")
config_app = typer.Typer(help="Run config utilities")
app.add_typer(config_app, name="config")

logger = structlog.get_logger()


def _resolve_config_path(config: Path) -> Path:
    return config.expanduser().resolve()


@app.command("version")
def version_cmd() -> None:
    typer.echo(__version__)


@config_app.command("validate")
def config_validate(
    config_path: Path = typer.Argument(..., help="Path to run.yaml or run.json"),
) -> None:
    """Load and validate a Run config."""
    try:
        svc = ConfigService()
        run_config = svc.load_run(_resolve_config_path(config_path))
        typer.echo(json.dumps(svc.validate_run(run_config), indent=2))
    except ConfigError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@app.command("window-pick")
def window_pick(
    title_rule: str = typer.Option(..., "--rule", help="Window title rule"),
) -> None:
    """List matching windows and bind by numeric choice (Window pick)."""
    svc = WindowService()
    try:
        windows = svc.list_matching(title_rule)
    except Exception as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    if not windows:
        typer.echo(f"No windows matched: {title_rule!r}", err=True)
        raise typer.Exit(1)
    for index, window in enumerate(windows, start=1):
        typer.echo(
            f"[{index}] handle={window.handle} {window.width}x{window.height} {window.title!r}"
        )
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
        merged = load_context(_resolve_config_path(config_path))
        cap_svc = CaptureService(log_dir=logs_dir())
        if fixture:
            cap_svc.use_fixture(fixture, merged.config.display_preset)
        else:
            cap_svc.bind(
                merged.config.window_title_rule,
                pick_handle,
                merged.config.display_preset,
            )
        frame = cap_svc.capture_frame()
        path = cap_svc.save_frame(frame, output)
        typer.echo(f"Saved {path} ({frame.width}x{frame.height})")
    except (ConfigError, WindowBindingError, CaptureError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc


@app.command("detect")
def detect_loop(
    config_path: Path = typer.Option(..., "--config", "-c"),
    catalog_dir_opt: Optional[Path] = typer.Option(None, "--catalog-dir"),
    iterations: int = typer.Option(5, "--iterations", "-n"),
    fixture: Optional[Path] = typer.Option(None, "--fixture"),
    pick_handle: Optional[int] = typer.Option(None, "--pick-handle"),
) -> None:
    """Detect-only loop: log Screen state transitions."""
    configure_logging()
    try:
        merged = load_context(_resolve_config_path(config_path))
        catalog = StateCatalog.from_directory(catalog_dir_opt or catalog_dir())
        capture = create_capture(
            merged.config,
            fixture=fixture,
            pick_handle=pick_handle,
        )
        controller = RunController(
            catalog=catalog,
            capture=capture,
            recognition_retries=merged.config.recognition_retries,
            log_dir=logs_dir(),
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
        merged = load_context(_resolve_config_path(config_path))
        if name not in merged.anchors:
            raise ConfigError(f"Anchor not in Anchor set: {name}")
        capture = create_capture(
            merged.config,
            fixture=fixture,
            pick_handle=pick_handle,
        )
        frame = capture.capture()
        matcher = ImageMatch()
        match = matcher.find(frame, merged.anchors[name])
        if match is None:
            typer.echo(f"No match for anchor {name!r}", err=True)
            raise typer.Exit(1)
        typer.echo(f"match score={match.score:.3f} center={match.center}")
        engine = ScriptEngine(
            controller=RunController(
                catalog=StateCatalog.from_directory(catalog_dir()),
                capture=capture,
                recognition_retries=1,
                log_dir=logs_dir(),
            ),
            capture=capture,
            matcher=matcher,
            ap_reader=FakeAPReader(),
            anchor_paths=merged.anchors,
            loop_limit=merged.config.loop_limit,
        )
        engine._click(match.center)
    except (ConfigError, WindowBindingError, CaptureError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc


@app.command("run")
def run_cmd(
    config_path: Path = typer.Option(default_run_config_path(), "--config", "-c"),
    catalog_dir_opt: Optional[Path] = typer.Option(None, "--catalog-dir"),
    fixture: Optional[Path] = typer.Option(None, "--fixture", help="Offline run with PNG fixture"),
    pick_handle: Optional[int] = typer.Option(None, "--pick-handle"),
    ap_insufficient_template: Optional[Path] = typer.Option(None, "--ap-insufficient-template"),
    battle_assist_template: Optional[Path] = typer.Option(None, "--battle-assist-template"),
    quest_profile: Optional[str] = typer.Option(None, "--quest-profile", help="Quest profile id (v2)"),
) -> None:
    """Start a Run (Quest loop v0)."""
    configure_logging()
    try:
        merged = load_context(_resolve_config_path(config_path))
        engine, controller = create_run_stack(
            merged,
            fixture=fixture,
            pick_handle=pick_handle,
            catalog_path=catalog_dir_opt,
            ap_insufficient_template=ap_insufficient_template,
            battle_assist_template=battle_assist_template,
            quest_profile=quest_profile,
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
