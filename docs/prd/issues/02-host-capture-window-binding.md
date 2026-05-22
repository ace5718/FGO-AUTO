# v1 slice: Host capture, Window binding, Display preset gate

GitHub: ace5718/FGO-AUTO#4

## Status

已關閉（main 已實作，pytest 通過）。

## Parent

PRD v1 Screen state and Quest loop.

## What to build

Bind exactly one BlueStacks TW FGO window using Window title rule from RunConfig. Verify Display preset 1920x1080 before Run proceeds. HostCapture returns frames; save diagnostic frame to log directory on demand. Refuse start when zero or multiple windows match (Window pick is a later slice).

## Acceptance criteria

- [x] With BlueStacks open at 1920x1080, CLI command captures one frame to log path
- [x] Wrong resolution or no matching window yields non-zero exit and clear message
- [x] WindowBinder unit-tested with fake window metadata; HostCapture uses fixture in tests
- [x] Default Window title rule documented after Operator calibration note in README

## Blocked by

Issue for slice 01 (CLI bootstrap and RunConfig)