# FGO-AUTO

Fate/Grand Order automation helper project.

**Version:** `0.2.0` (see `VERSION` and [CHANGELOG.md](CHANGELOG.md))

## Development setup (venv)

Use a project-local virtual environment at `venv/` (already in `.gitignore`).

```powershell
cd D:\FGO-AUTO
.\scripts\setup-venv.ps1
.\venv\Scripts\Activate.ps1
fgo-auto version
python -m pytest -q
```

Manual steps:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,windows,gui]"
```

Always activate `venv` before running `fgo-auto` or `pytest`. Cursor terminal: select the Python interpreter at `venv\Scripts\python.exe`.


## Desktop app (GUI)

Local **CustomTkinter** window; data stays on disk under `data/` ([ADR-0004](docs/adr/0004-desktop-ui-customtkinter.md)).

```powershell
pip install -e ".[dev,windows,gui]"
.\scripts\init-local-profile.ps1
fgo-auto-gui
```

| Tab | Purpose |
|-----|---------|
| Run | Window pick, Start / Manual stop, Screen state |
| 設定 | Edit and save `data/profiles/default/run.yaml` |
| 預覽 | Capture frame thumbnail to `logs/frame.png` |
| 日誌 | Live structlog output |
| Catalog | Phase 2 stub |

Manual checklist: [docs/manual-test-gui.md](docs/manual-test-gui.md).

## Operator quick start (v1 CLI)

TW FGO on **BlueStacks 5**, **1920x1080** ([ADR-0001](docs/adr/0001-fixed-bluestacks-display-preset.md)).

```powershell
.\venv\Scripts\Activate.ps1
fgo-auto config validate examples/run.example.yaml
fgo-auto capture-frame -c examples/run.example.yaml -o logs/frame.png
fgo-auto run -c examples/run.example.yaml
```

| Command | Purpose |
|---------|---------|
| `fgo-auto capture-frame -c examples/run.example.yaml -o logs/frame.png` | Bind window, verify resolution, save one frame |
| `fgo-auto detect -c examples/run.example.yaml` | Screen state detect-only loop |
| `fgo-auto tap-anchor -c examples/run.example.yaml -n enter_quest` | Match one Quest anchor and tap |
| `fgo-auto run -c examples/run.example.yaml` | Quest loop v0 |
| `fgo-auto window-pick --rule BlueStacks` | Window pick when multiple windows match |

Calibrate `window_title_rule` in [examples/run.example.yaml](examples/run.example.yaml). Add Screen catalog PNGs under [catalog/](catalog/). Automation may violate game terms; use at your own risk.

## Agent setup (Cursor)

This repo includes [mattpocock/skills](https://github.com/mattpocock/skills).

```bash
npx skills@latest add mattpocock/skills
```

- Skills: `.agents/skills/`
- Agent guide: `AGENTS.md`
- Domain glossary: `CONTEXT.md`
- ADRs: `docs/adr/`

### Suggested workflow (Cursor)

| Purpose | Skill |
|---------|--------|
| New feature / unclear requirements | `@grill-with-docs` |
| Implement code | `@tdd` |
| Debug | `@diagnose` |
| Large tasks | `to-prd` then `to-issues` |

Create GitHub labels if missing: needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix.

## v0.2（Quest profile + 導航／戰鬥腳本）

- script_version: v0（預設）維持 v0.1 行為；2 需 quest_profile。
- 範例關卡：examples/quests/treasure_door_extreme/（
avigation.yaml、attle.yaml）。
- Catalog 依 display_preset 載入：data/catalog/{width}x{height}/（見 ADR-0005）。
- CLI：go-auto run -c run.yaml --quest-profile treasure_door_extreme
- GUI：設定分頁可選 v2 與關卡 id；模板庫分頁可列出 catalog 子目錄。

手動驗收清單：docs/manual-test-v0.2.md

