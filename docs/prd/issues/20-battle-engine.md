# v0.2 slice: BattleScriptEngine turn executor

GitHub: ace5718/FGO-AUTO#20

## Status

開啟（已發布至 GitHub）

## Parent

PRD v0.2.0 (#11).

## What to build

Execute battle turns: tap skill buttons, select command cards in order, trigger NP. Timeouts and retries per action. Run pause on recognition failure.

## Acceptance criteria

- [ ] Fixture test runs 2-turn script without live game
- [ ] Logs each action type and outcome
- [ ] Manual stop aborts battle loop
- [ ] craft_skill and servant_skill use normalized or anchor taps

## Blocked by

- #18 (18-battle-dsl.md)
- #19 (19-battle-catalog.md)