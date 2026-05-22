from __future__ import annotations

import queue
import sys
from pathlib import Path

import customtkinter as ctk

from fgo_auto.logging_setup import configure_logging
from fgo_auto.run.controller import RunOutcome
from fgo_auto.run_config import RunConfig
from fgo_auto.services.capture_service import CaptureService
from fgo_auto.services.config_service import ConfigService
from fgo_auto.services.paths import default_profile_dir, logs_dir
from fgo_auto.services.run_service import RunEventType, RunService
from fgo_auto.services.run_setup import create_run_stack
from fgo_auto.ui.logging_bridge import attach_queue_handler
from fgo_auto.ui.pages import CatalogPage, LogsPage, PreviewPage, RunPage, SettingsPage
from fgo_auto.ui.state import AppState
from fgo_auto.ui.widgets import WindowPickerFrame


class FgoAutoApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("FGO-AUTO")
        self.geometry("1000x720")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        configure_logging()
        self._log_queue: queue.Queue[str] = queue.Queue()
        attach_queue_handler(self._log_queue)

        self._config_svc = ConfigService()
        self._config_svc.seed_default_profile()
        self._capture_svc = CaptureService(log_dir=logs_dir())
        self._run_svc: RunService | None = None
        self._state = AppState(profile_dir=default_profile_dir())

        self._build_ui()
        self._load_profile()
        self.after(100, self._poll_run_events)

    def _build_ui(self) -> None:
        self._tabs = ctk.CTkTabview(self)
        self._tabs.pack(fill="both", expand=True, padx=12, pady=12)

        tab_run = self._tabs.add("Run")
        tab_settings = self._tabs.add("設定")
        tab_preview = self._tabs.add("預覽")
        tab_logs = self._tabs.add("日誌")
        tab_catalog = self._tabs.add("Catalog")

        self._window_picker = WindowPickerFrame(tab_run, on_select=self._on_window_selected)
        self._window_picker.pack(fill="x", padx=8, pady=8)

        self._run_page = RunPage(tab_run, on_start=self._start_run, on_stop=self._stop_run)
        self._run_page.pack(fill="both", expand=True)

        self._settings_page = SettingsPage(
            tab_settings,
            on_save=self._save_config,
            on_validate=self._validate_config,
        )
        self._settings_page.pack(fill="both", expand=True)

        self._preview_page = PreviewPage(tab_preview, on_capture=self._capture_preview)
        self._preview_page.pack(fill="both", expand=True)

        self._logs_page = LogsPage(tab_logs, self._log_queue)
        self._logs_page.pack(fill="both", expand=True)

        self._catalog_page = CatalogPage(tab_catalog)
        self._catalog_page.pack(fill="both", expand=True)

        footer = ctk.CTkLabel(self, text=f"Local data root: {self._state.profile_dir.parent.parent}")
        footer.pack(anchor="w", padx=16, pady=(0, 8))

    def _load_profile(self) -> None:
        try:
            cfg = self._config_svc.load_run()
            self._state.run_config = cfg
            self._settings_page.load_config(cfg)
            self._window_picker.set_rule(cfg.window_title_rule)
        except Exception as exc:
            self._run_page.update_status(message=f"載入設定失敗：{exc}")

    def _save_config(self, config: RunConfig) -> None:
        self._config_svc.save_run(config)
        self._state.run_config = config
        self._window_picker.set_rule(config.window_title_rule)

    def _validate_config(self, config: RunConfig) -> dict:
        return self._config_svc.validate_run(config)

    def _on_window_selected(self, handle: int, title: str) -> None:
        self._state.pick_handle = handle
        self._state.bound_window_title = title

    def _capture_preview(self) -> Path:
        if self._state.run_config is None:
            raise RuntimeError("請先載入 Run config")
        cfg = self._state.run_config
        if self._state.pick_handle is None:
            raise RuntimeError("請先在 Run 分頁選擇視窗")
        self._capture_svc.bind(cfg.window_title_rule, self._state.pick_handle, cfg.display_preset)
        frame = self._capture_svc.capture_frame()
        path = self._capture_svc.save_frame(frame, "frame.png")
        self._state.last_capture_path = path
        return path

    def _start_run(self) -> str:
        if self._run_svc and self._run_svc.is_running():
            return "Run 已在執行中"
        if self._state.run_config is None:
            return "請先儲存 Run 設定"
        if self._state.pick_handle is None:
            return "請先綁定 BlueStacks 視窗"
        try:
            merged = self._config_svc.load_merged()
            engine, _controller = create_run_stack(
                merged,
                pick_handle=self._state.pick_handle,
            )
            self._run_svc = RunService(engine)
            self._run_svc.start()
            self._state.run_active = True
            return "Run 已啟動（背景執行緒）"
        except Exception as exc:
            return f"啟動失敗：{exc}"

    def _stop_run(self) -> None:
        if self._run_svc:
            self._run_svc.stop()

    def _poll_run_events(self) -> None:
        if self._run_svc:
            while True:
                try:
                    event = self._run_svc.events.get_nowait()
                except queue.Empty:
                    break
                if event.type is RunEventType.SCREEN_STATE and event.screen_state:
                    self._state.last_screen_state = event.screen_state.value
                    self._run_page.update_status(
                        screen_state=event.screen_state.value,
                        loops=event.loops_completed,
                    )
                elif event.type is RunEventType.OUTCOME:
                    self._state.run_active = False
                    msg = event.message
                    if event.outcome is RunOutcome.PAUSED:
                        msg += " — 請查看 logs/pause_screenshot.png"
                    self._run_page.update_status(
                        outcome=event.outcome,
                        loops=event.loops_completed,
                        message=msg,
                    )
                elif event.type is RunEventType.ERROR:
                    self._state.run_active = False
                    self._run_page.update_status(message=event.message)
        self.after(200, self._poll_run_events)


def main() -> None:
    if sys.platform == "win32":
        try:
            from ctypes import windll

            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    app = FgoAutoApp()
    app.mainloop()


if __name__ == "__main__":
    main()
