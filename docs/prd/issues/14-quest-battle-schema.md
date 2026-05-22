# v0.2 slice: Quest profile and script schemas (navigation + battle)

GitHub: ace5718/FGO-AUTO#14

## Status

開啟（已發布至 GitHub）

## Parent

PRD v0.2.0 (#11).

## What to build

Pydantic models: `QuestProfile`, `NavigationScript`, `BattleScript`. Example under `examples/quests/treasure_door_extreme/` with navigation + battle YAML. Load/validate via ConfigService extension or new loader.

## Acceptance criteria

- [ ] Example profile `treasure_door_extreme` documents chaldea → daily → door extreme flow
- [ ] Invalid YAML fails validation with clear errors
- [ ] `friend_support` and `party_slot` fields present (may be anchor-only in v0.2)
- [ ] Unit tests for schema round-trip

## Blocked by

- #12 (12-adr-display-preset.md)