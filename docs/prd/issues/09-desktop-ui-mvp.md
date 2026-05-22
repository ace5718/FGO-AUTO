# Issue 09 — Desktop UI MVP (CustomTkinter)

GitHub: ace5718/FGO-AUTO#9

## Status

Implemented in repo (service layer + `fgo-auto-gui`). Close #9 after merge to `main`.

## Acceptance (maps to #9)

- [x] `fgo-auto-gui` entry point; `pip install -e ".[windows,gui]"`
- [x] ConfigService save/load Run config YAML locally (`data/profiles/`)
- [x] Window picker UI (Run tab)
- [x] Capture preview (thumbnail + `logs/frame.png`)
- [x] Background Run thread + Manual stop; Screen state + outcome
- [x] ADR-0004, README, `docs/manual-test-gui.md`

## Follow-up

Phase 2: #10 anchor/catalog visual editor.
