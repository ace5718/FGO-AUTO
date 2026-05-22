# v0.2 slice: Battle sub-screen catalog (command / skill / NP)

GitHub: ace5718/FGO-AUTO#19

## Status

開啟（已發布至 GitHub）

## Parent

PRD v0.2.0 (#11).

## What to build

Catalog templates for battle phases: command card select, skill menu open, NP cut-in detect (minimal set). Map to Screen state or custom states battle_command, battle_skill_menu.

## Acceptance criteria

- [ ] At least one fixture template per battle phase for tests
- [ ] detect identifies battle vs non-battle
- [ ] Document TW UI assumptions in profile README

## Blocked by

- #13 (13-catalog-pack-tap-api.md)