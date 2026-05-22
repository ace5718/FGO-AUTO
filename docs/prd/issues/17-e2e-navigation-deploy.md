# v0.2 slice: E2E Run from main menu to deploy (寶物庫之門極)

GitHub: ace5718/FGO-AUTO#17

## Status

開啟（已發布至 GitHub）

## Parent

PRD v0.2.0 (#11).

## What to build

Wire v0.2 quest profile into `fgo-auto run` and GUI Start: `script_version: v2`, `--quest-profile treasure_door_extreme`. End-to-end navigation only (battle may noop or stub) with fixture sequence proving step order.

## Acceptance criteria

- [ ] CLI flag loads quest profile from `data/profiles/` or examples
- [ ] Run stops with clear error if anchor missing
- [ ] Integration test: fixture frames simulate menu transitions
- [ ] GUI shows navigation phase in logs

## Blocked by

- #16 (16-navigation-engine.md)