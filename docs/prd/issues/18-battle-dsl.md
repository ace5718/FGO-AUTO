# v0.2 slice: Battle script DSL validation and docs

GitHub: ace5718/FGO-AUTO#18

## Status

開啟（已發布至 GitHub）

## Parent

PRD v0.2.0 (#11).

## What to build

Validate battle YAML: turns, actions types servant_skill, craft_skill, select_cards, noble_phantasm. Document fields (slot, skill index, cards order). Example `battle/farm_door.yaml`.

## Acceptance criteria

- [ ] Pydantic models reject unknown action types
- [ ] Example battle script in examples/quests/treasure_door_extreme/
- [ ] README section for battle script authoring
- [ ] pytest schema tests

## Blocked by

- #14 (14-quest-battle-schema.md)