from __future__ import annotations

import re

from fgo_auto.run.controller import RunOutcome

# 畫面狀態（Screen state）顯示名稱
SCREEN_STATE_ZH: dict[str, str] = {
    "unknown": "未知",
    "main": "主畫面",
    "terminal": "禮裝介面",
    "battle": "戰鬥",
    "result": "結果畫面",
}

OUTCOME_ZH: dict[RunOutcome, str] = {
    RunOutcome.RUNNING: "執行中",
    RunOutcome.NORMAL_END: "正常結束",
    RunOutcome.PAUSED: "執行暫停",
}

_ERROR_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"Display preset mismatch: got (\d+)x(\d+), expected (\d+)x(\d+)",
            re.I,
        ),
        r"顯示尺寸不符：目前 \1×\2，設定要求 \3×\4。請將 BlueStacks 視窗調為與 run.yaml 的 display_preset 一致（見 ADR-0005）。",
    ),
    (re.compile(r"No windows matched", re.I), "找不到符合規則的視窗"),
    (re.compile(r"Run config not found", re.I), "找不到 Run 設定檔"),
    (re.compile(r"No window bound", re.I), "尚未綁定視窗，請先選擇 BlueStacks"),
    (
        re.compile(r"script_version v2 requires quest_profile", re.I),
        "腳本版本 v2 必須填寫關卡設定檔（quest_profile），請到「設定」輸入例如 treasure_door_extreme 後儲存",
    ),
]


def screen_state_label(value: str) -> str:
    return SCREEN_STATE_ZH.get(value, value)


def outcome_label(outcome: RunOutcome) -> str:
    return OUTCOME_ZH.get(outcome, outcome.value)


def recognition_pause_hint(display_preset: tuple[int, int] | None = None) -> str:
    size = f"{display_preset[0]}×{display_preset[1]}" if display_preset else "與 BlueStacks 視窗一致"
    return (
        f"畫面辨識失敗：{size} 的模板庫可能為空或與目前畫面不符。"
        "請到「模板庫」→「擷圖→存為主畫面模板」（遊戲停在主畫面），再執行。"
        "詳情見 logs/pause_screenshot.png。"
    )


def translate_message(text: str) -> str:
    for pattern, repl in _ERROR_PATTERNS:
        if pattern.search(text):
            return pattern.sub(repl, text)
    return text
