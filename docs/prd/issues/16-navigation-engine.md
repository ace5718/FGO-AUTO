# v0.2 slice: NavigationEngine step runner

GitHub: ace5718/FGO-AUTO#16

## Status

開啟（已發布至 GitHub）

## Parent

PRD v0.2.0 (#11).

## What to build

`NavigationEngine` executes navigation YAML steps: tap_anchor, wait_screen, wait_anchor, delay. Integrate with RunController for recognition retry and Run pause. Log each step.

## Acceptance criteria

- [ ] Steps run in order; failure enters Run pause
- [ ] Works with InMemory/fixture capture in pytest
- [ ] RunService can invoke navigation phase before battle
- [ ] structlog events include step index and anchor name

## Blocked by

- #15 (15-navigation-catalog-anchors.md)