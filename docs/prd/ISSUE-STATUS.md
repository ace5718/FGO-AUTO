# GitHub Issue 狀態（ace5718/FGO-AUTO）

最後更新：2026-05-22（v0.2.0 程式已合入工作區）

## v0.2.0（程式已實作，待 merge 後關閉 issues）

| # | 標題 | 程式狀態 |
|---|------|----------|
| 11 | PRD: v0.2.0 | 文件完成 |
| 12 | ADR-0005 / 顯示尺寸訊息 | `capture.py`、`strings_zh.py` |
| 13 | Catalog 分包 + tap | `paths.catalog_dir_for_preset`、`host/tap.py` |
| 14 | Quest schema | `quest/`、`RunConfig.script_version` |
| 15 | 導航錨點文件 | `examples/quests/treasure_door_extreme/README.md` |
| 16 | NavigationEngine | `script/navigation.py` |
| 17 | E2E / CLI | `engine_v2.py`、`--quest-profile` |
| 18–21 | Battle | `battle_script.py` + `ScriptEngineV2` |
| 22 | GUI | 設定分頁 `script_version` / `quest_profile` |
| 23 | 錨點/catalog | `ConfigService.save_anchor_crop`、`list_catalog_states` |
| 24 | 發版 | `VERSION` 0.2.0、README v0.2 章節 |

驗收：`pytest` 30 passed；預設 `script_version: v0` 維持回歸。

## v0.1 / UI

| # | 標題 | 狀態 |
|---|------|------|
| 1–9 | v1 + Desktop UI | 已關閉 |
| 10 | Phase 2 視覺編輯 | 開啟（#23 已最小實作，完整框選 UI 可後續） |

## 本地對照

- PRD：`docs/prd/0002-v0.2-full-quest-and-battle-script.md`
- 範例：`examples/quests/treasure_door_extreme/`
- 手動測試：`docs/manual-test-v0.2.md`
