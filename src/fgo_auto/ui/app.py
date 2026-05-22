from __future__ import annotations

import queue
import sys
from pathlib import Path

import customtkinter as ctk

from fgo_auto.logging_setup import configure_logging
from fgo_auto.run.controller import RunOutcome
from fgo_auto.run.run_config import RunConfig
from fgo_auto.services.capture_service import CaptureService
from fgo_auto.services.config_service import ConfigService
from fgo_auto.services.paths import default_profile_dir, logs_dir
from fgo_auto.services.catalog_service import count_templates
from fgo_auto.services.quest_flow_service import list_user_quest_profiles
from fgo_auto.services.run_service import RunEventType, RunService
from fgo_auto.services.run_setup import create_run_stack
from fgo_auto.ui.pages import (
    AnchorsPage,
    CatalogPage,
    FlowPage,
    LogsPage,
    PreviewPage,
    RunPage,
    SettingsPage,
)
from fgo_auto.ui.state import AppState
from fgo_auto.ui.strings_zh import recognition_pause_hint, screen_state_label, translate_message
from fgo_auto.ui.widgets import WindowPickerFrame


class FgoAutoApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("FGO-AUTO 自動化")
        self.geometry("1000x720")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self._log_queue: queue.Queue[str] = queue.Queue()
        configure_logging(gui_queue=self._log_queue)

        self._config_svc = ConfigService()
        self._config_svc.seed_default_profile()
        self._capture_svc = CaptureService(log_dir=logs_dir())
        self._run_svc: RunService | None = None
        self._state = AppState(profile_dir=default_profile_dir())

        self._build_ui()
        self._load_profile()
        self._refresh_run_quest_menu()
        self.after(100, self._poll_run_events)

    def _build_ui(self) -> None:
        self._tabs = ctk.CTkTabview(self)
        self._tabs.pack(fill="both", expand=True, padx=12, pady=12)

        tab_run = self._tabs.add("執行")
        tab_flow = self._tabs.add("流程設定")
        tab_anchors = self._tabs.add("圖示庫")
        tab_settings = self._tabs.add("設定")
        tab_preview = self._tabs.add("預覽")
        tab_logs = self._tabs.add("日誌")
        tab_catalog = self._tabs.add("模板庫")

        self._window_picker = WindowPickerFrame(tab_run, on_select=self._on_window_selected)
        self._window_picker.pack(fill="x", padx=8, pady=8)

        self._run_page = RunPage(
            tab_run,
            on_start=self._start_run,
            on_stop=self._stop_run,
            on_apply_run_quest=self._apply_run_quest,
        )
        self._run_page.pack(fill="both", expand=True)

        self._settings_page = SettingsPage(
            tab_settings,
            on_save=self._save_config,
            on_validate=self._validate_config,
        )
        self._settings_page.pack(fill="both", expand=True)

        self._flow_page = FlowPage(
            tab_flow,
            on_apply_quest_profile=self._apply_quest_profile,
            on_quest_selected=self._on_flow_quest_selected,
        )
        self._flow_page.pack(fill="both", expand=True)

        self._anchors_page = AnchorsPage(
            tab_anchors,
            on_go_preview=lambda: self._focus_tab("預覽"),
        )
        self._anchors_page.pack(fill="both", expand=True)

        self._preview_page = PreviewPage(
            tab_preview,
            on_capture=self._capture_preview,
            get_quest_id=self._preview_quest_id,
            on_anchor_saved=self._on_anchor_saved,
        )
        self._preview_page.pack(fill="both", expand=True)

        self._logs_page = LogsPage(tab_logs, self._log_queue)
        self._logs_page.pack(fill="both", expand=True)

        self._catalog_page = CatalogPage(tab_catalog, on_capture=self._capture_preview)
        self._catalog_page.pack(fill="both", expand=True)

        footer = ctk.CTkLabel(
            self,
            text=f"本機資料目錄：{self._state.profile_dir.parent.parent}",
        )
        footer.pack(anchor="w", padx=16, pady=(0, 8))

    def _load_profile(self) -> None:
        try:
            cfg = self._config_svc.load_run()
            self._state.run_config = cfg
            self._settings_page.load_config(cfg)
            self._window_picker.set_rule(cfg.window_title_rule)
        except Exception as exc:
            self._run_page.update_status(message=f"載入設定失敗：{translate_message(str(exc))}")

    def _save_config(self, config: RunConfig) -> None:
        self._config_svc.save_run(config)
        self._state.run_config = config
        self._window_picker.set_rule(config.window_title_rule)
        self._refresh_run_flow_status()

    def _refresh_run_quest_menu(self) -> None:
        entries = list_user_quest_profiles()
        items = [(e.quest_id, f"{e.display_name or e.quest_id}") for e in entries]
        active = self._state.run_config.quest_profile if self._state.run_config else None
        if self._state.editing_quest_id:
            active = self._state.editing_quest_id
        self._run_page.set_quest_choices(items, active)
        self._refresh_run_flow_status()

    def _refresh_run_flow_status(self) -> None:
        cfg = self._state.run_config
        if cfg is None:
            return
        self._run_page.show_active_flow(cfg.quest_profile, cfg.script_version)

    def _apply_run_quest(self, quest_id: str) -> None:
        self._apply_quest_profile(quest_id)
        try:
            if self._state.run_config:
                self._config_svc.save_run(self._state.run_config)
            self._refresh_run_flow_status()
            self._run_page.update_status(message=f"已套用流程 {quest_id} 並寫入設定，可開始執行")
        except Exception as exc:
            self._run_page.update_status(message=translate_message(str(exc)))

    def _validate_config(self, config: RunConfig) -> dict:
        return self._config_svc.validate_run(config)

    def _current_quest_id(self) -> str | None:
        cfg = self._state.run_config
        if cfg is None or not cfg.quest_profile:
            return None
        text = str(cfg.quest_profile).strip()
        return text or None

    def _preview_quest_id(self) -> str | None:
        if self._state.editing_quest_id:
            return self._state.editing_quest_id
        return self._current_quest_id()

    def _on_flow_quest_selected(self, quest_id: str) -> None:
        self._state.editing_quest_id = quest_id
        self._preview_page.refresh_quest()
        self._anchors_page.select_quest(quest_id)

    def _on_anchor_saved(self) -> None:
        self._flow_page.reload()
        self._anchors_page.reload()
        self._flow_page.refresh_anchor_choices()

    def _focus_tab(self, tab_name: str, quest_id: str | None = None) -> None:
        self._tabs.set(tab_name)
        if quest_id:
            self._state.editing_quest_id = quest_id
            self._anchors_page.select_quest(quest_id)
            self._preview_page.refresh_quest()

    def _apply_quest_profile(self, quest_id: str) -> None:
        if self._state.run_config is None:
            try:
                self._state.run_config = self._config_svc.load_run()
            except Exception:
                return
        cfg = self._state.run_config.model_copy(
            update={"quest_profile": quest_id, "script_version": "v2"}
        )
        self._state.run_config = cfg
        self._settings_page.load_config(cfg)
        self._state.editing_quest_id = quest_id
        self._preview_page.refresh_quest()
        self._anchors_page.select_quest(quest_id)
        self._refresh_run_quest_menu()

    def _on_window_selected(self, handle: int, title: str) -> None:
        self._state.pick_handle = handle
        self._state.bound_window_title = title

    def _capture_preview(self) -> Path:
        if self._state.run_config is None:
            raise RuntimeError("請先在「設定」分頁載入並儲存 Run 設定")
        cfg = self._state.run_config
        if self._state.pick_handle is None:
            raise RuntimeError("請先在「執行」分頁綁定 BlueStacks 視窗")
        self._capture_svc.bind(cfg.window_title_rule, self._state.pick_handle, cfg.display_preset)
        frame = self._capture_svc.capture_frame()
        path = self._capture_svc.save_frame(frame, "frame.png")
        self._state.last_capture_path = path
        self._config_svc.save_preview_frame(path)
        return path

    def _start_run(self) -> str:
        if self._run_svc and self._run_svc.is_running():
            return "已有執行中的 Run，請先按「手動停止」"
        if self._state.run_config is None:
            return "請先在「設定」分頁儲存 Run 設定"
        if self._state.pick_handle is None:
            return "請先在「執行」分頁選擇 BlueStacks 視窗"
        quest_id = self._run_page.selected_quest_id() or self._state.editing_quest_id
        if quest_id:
            self._apply_quest_profile(quest_id)
            try:
                self._config_svc.save_run(self._state.run_config)  # type: ignore[arg-type]
            except Exception:
                pass
        cfg = self._state.run_config
        if cfg and cfg.script_version == "v2" and not cfg.quest_profile:
            return "v2 請在「執行」選擇流程並按「套用此流程」，或到流程設定套用後儲存設定"
        try:
            merged = self._config_svc.load_merged()
            engine, _controller = create_run_stack(
                merged,
                pick_handle=self._state.pick_handle,
            )
            self._run_svc = RunService(engine)
            self._run_svc.start()
            self._state.run_active = True
            qid = cfg.quest_profile if cfg else "—"
            ver = cfg.script_version if cfg else "—"
            n = count_templates(cfg.display_preset)
            start_msg = f"已開始執行（{ver} · {qid}）"
            self._logs_page.append_line(start_msg)
            if n == 0:
                self._logs_page.append_line(
                    f"警告：{cfg.display_preset[0]}×{cfg.display_preset[1]} 模板庫為空，"
                    "請到「模板庫」→「擷圖→存為主畫面模板」（遊戲需在主畫面）"
                )
            return start_msg
        except Exception as exc:
            msg = translate_message(f"啟動失敗：{exc}")
            self._log_queue.put(msg)
            self._logs_page.append_line(msg)
            return msg

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
                    line = (
                        f"畫面：{screen_state_label(event.screen_state.value)}"
                        f"（{event.screen_state.value}）循環 {event.loops_completed}"
                    )
                    self._logs_page.append_line(line)
                    self._run_page.update_status(
                        screen_state=event.screen_state.value,
                        loops=event.loops_completed,
                    )
                elif event.type is RunEventType.OUTCOME:
                    self._state.run_active = False
                    msg = translate_message(event.message)
                    if event.outcome is RunOutcome.PAUSED:
                        preset = (
                            self._state.run_config.display_preset
                            if self._state.run_config
                            else None
                        )
                        if "Recognition failure" in event.message or "recognition" in event.message.lower():
                            msg = recognition_pause_hint(preset)
                        else:
                            msg += " — 請查看 logs/pause_screenshot.png"
                    self._logs_page.append_line(f"結果：{msg}")
                    self._run_page.update_status(
                        outcome=event.outcome,
                        loops=event.loops_completed,
                        message=msg,
                    )
                elif event.type is RunEventType.ERROR:
                    self._state.run_active = False
                    err = translate_message(event.message)
                    self._logs_page.append_line(f"錯誤：{err}")
                    self._run_page.update_status(message=err)
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
