from __future__ import annotations

from pathlib import Path

from fgo_auto.host.capture import CaptureError, HostCapture
from fgo_auto.host.window_binder import WindowBinder
from fgo_auto.run.controller import RunController
from fgo_auto.run_config import RunConfig
from fgo_auto.script.ap_reader import APReader, FakeAPReader, TemplateAPReader
from fgo_auto.script.engine import ScriptEngine
from fgo_auto.services.capture_service import CaptureService
from fgo_auto.services.config_service import ConfigService, MergedRunContext
from fgo_auto.services.paths import catalog_dir, logs_dir
from fgo_auto.services.run_service import build_script_engine
from fgo_auto.vision.state_catalog import StateCatalog


def load_context(config_path: Path | None = None) -> MergedRunContext:
    svc = ConfigService()
    svc.seed_default_profile()
    if config_path:
        return svc.load_merged(config_path)
    return svc.load_merged()


def create_capture(
    config: RunConfig,
    *,
    fixture: Path | None = None,
    pick_handle: int | None = None,
    binder: WindowBinder | None = None,
) -> HostCapture:
    svc = CaptureService(binder=binder, log_dir=logs_dir())
    if fixture:
        svc.use_fixture(fixture, config.display_preset)
    else:
        svc.bind(config.window_title_rule, pick_handle, config.display_preset)
    backend = svc.capture_backend
    if backend is None:
        raise CaptureError("Capture backend not initialized")
    return backend


def create_run_stack(
    merged: MergedRunContext,
    *,
    fixture: Path | None = None,
    pick_handle: int | None = None,
    catalog_path: Path | None = None,
    ap_insufficient_template: Path | None = None,
    battle_assist_template: Path | None = None,
    binder: WindowBinder | None = None,
) -> tuple[ScriptEngine, RunController]:
    config = merged.config
    capture = create_capture(
        config,
        fixture=fixture,
        pick_handle=pick_handle,
        binder=binder,
    )
    catalog = StateCatalog.from_directory(catalog_path or catalog_dir())
    controller = RunController(
        catalog=catalog,
        capture=capture,
        recognition_retries=config.recognition_retries,
        log_dir=logs_dir(),
    )
    ap_reader: APReader = (
        TemplateAPReader(ap_insufficient_template)
        if ap_insufficient_template
        else FakeAPReader(True)
    )
    engine = build_script_engine(
        controller,
        merged.anchors,
        config.loop_limit,
        battle_assist_template=battle_assist_template,
        ap_reader=ap_reader,
    )
    return engine, controller
