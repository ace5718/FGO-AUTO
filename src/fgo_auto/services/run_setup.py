from __future__ import annotations

from pathlib import Path
from typing import Union

from fgo_auto.host.capture import CaptureError, HostCapture
from fgo_auto.host.window_binder import WindowBinder
from fgo_auto.quest.loader import resolve_quest_profile_dir
from fgo_auto.run.controller import RunController
from fgo_auto.run_config import RunConfig
from fgo_auto.script.ap_reader import APReader, FakeAPReader, TemplateAPReader
from fgo_auto.script.engine import ScriptEngine
from fgo_auto.script.engine_v2 import ScriptEngineV2, create_script_engine_v2
from fgo_auto.services.capture_service import CaptureService
from fgo_auto.services.config_service import ConfigService, MergedRunContext
from fgo_auto.services.paths import catalog_dir_for_preset, logs_dir
from fgo_auto.services.run_service import build_script_engine
from fgo_auto.vision.frame import Frame
from fgo_auto.vision.state_catalog import StateCatalog

ScriptEngineLike = Union[ScriptEngine, ScriptEngineV2]


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


def _quest_anchor_paths(quest_id: str, base_anchors: dict[str, Path]) -> dict[str, Path]:
    from fgo_auto.services.paths import data_root

    merged = dict(base_anchors)
    shared = data_root() / "anchors"
    if shared.is_dir():
        for png in shared.glob("*.png"):
            if png.is_file() and not png.name.startswith("_"):
                merged.setdefault(png.stem, png)
    try:
        quest_dir = resolve_quest_profile_dir(quest_id)
    except Exception:
        return merged
    quest_anchors_dir = quest_dir / "anchors"
    if quest_anchors_dir.is_dir():
        for png in quest_anchors_dir.glob("*.png"):
            if png.is_file():
                merged[png.stem] = png
    return merged


def create_run_stack(
    merged: MergedRunContext,
    *,
    fixture: Path | None = None,
    pick_handle: int | None = None,
    catalog_path: Path | None = None,
    runtime_catalog_frame: Frame | None = None,
    ap_insufficient_template: Path | None = None,
    battle_assist_template: Path | None = None,
    binder: WindowBinder | None = None,
    quest_profile: str | None = None,
) -> tuple[ScriptEngineLike, RunController]:
    config = merged.config
    capture = create_capture(
        config,
        fixture=fixture,
        pick_handle=pick_handle,
        binder=binder,
    )
    preset = config.display_preset
    if runtime_catalog_frame is not None:
        catalog = StateCatalog.from_runtime_session(runtime_catalog_frame)
    elif catalog_path is not None:
        catalog = StateCatalog.from_directory(catalog_path)
    else:
        catalog = StateCatalog.from_directory(
            catalog_dir_for_preset(preset[0], preset[1])
        )
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

    effective_quest = quest_profile or config.quest_profile
    if config.script_version == "v2":
        if not effective_quest:
            raise CaptureError("script_version v2 requires quest_profile")
        anchors = _quest_anchor_paths(effective_quest, merged.anchors)
        engine = create_script_engine_v2(
            controller,
            effective_quest,
            anchors,
            loop_limit=config.loop_limit,
            ap_reader=ap_reader,
        )
        return engine, controller

    engine = build_script_engine(
        controller,
        merged.anchors,
        config.loop_limit,
        battle_assist_template=battle_assist_template,
        ap_reader=ap_reader,
    )
    return engine, controller
