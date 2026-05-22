# v0.2 slice: Screen states and anchors for 迦勒底之門 → 寶物庫之門極

GitHub: ace5718/FGO-AUTO#15

## Status

開啟（已發布至 GitHub）

## Parent

PRD v0.2.0 (#11).

## What to build

Define anchor names and catalog entries for: chaldea_gate, daily_quests, door_treasure_extreme, friend_support steps, party_setup, deploy_confirm. Document in profile README. `fgo-auto detect` recognizes new states where templates exist.

## Acceptance criteria

- [ ] Anchor naming table in `examples/quests/treasure_door_extreme/README.md`
- [ ] At least fixture PNGs for detect tests (synthetic or committed samples)
- [ ] Screen states extended if needed (e.g. chaldea_menu, daily_menu)
- [ ] Operator doc: how to capture TW templates at their preset

## Blocked by

- #13 (13-catalog-pack-tap-api.md)
- #14 (14-quest-battle-schema.md)