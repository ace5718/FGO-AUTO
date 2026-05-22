# v0.2 slice: Integrate battle script after navigation (full loop)

GitHub: ace5718/FGO-AUTO#21

## Status

開啟（已發布至 GitHub）

## Parent

PRD v0.2.0 (#11).

## What to build

After deploy, run battle script until result screen; hook into quest loop iteration (result → repeat navigation or END). v0.2 Run completes one full 寶物庫之門極 sortie in test fixtures.

## Acceptance criteria

- [ ] Navigation → battle → wait result → loop counter
- [ ] Loop limit and AP check still apply
- [ ] Run pause screenshot on battle recognition failure
- [ ] pytest full v2 path with fakes

## Blocked by

- #20 (20-battle-engine.md)