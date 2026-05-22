# v1 follow-up: Window pick when multiple BlueStacks windows match

GitHub: ace5718/FGO-AUTO#8

## Status

已關閉（main 已實作，pytest 通過）。

## Parent

PRD v1 Screen state and Quest loop.

## What to build

When Window title rule matches more than one window, CLI lists candidates and Operator selects via Window pick. Selected window binds for the Run.

## Acceptance criteria

- [x] Multiple match shows numbered list; single selection binds window
- [x] Operator can cancel without starting Run
- [x] Documented in Run config README

## Blocked by

Issue for slice 02 (Host capture)