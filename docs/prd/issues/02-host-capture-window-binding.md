# v1 slice: Host capture, Window binding, Display preset gate

## Parent

PRD v1 Screen state and Quest loop.

## What to build

Bind exactly one BlueStacks TW FGO window using Window title rule from RunConfig. Verify Display preset 1920x1080 before Run proceeds. HostCapture returns frames; save diagnostic frame to log directory on demand. Refuse start when zero or multiple windows match (Window pick is a later slice).

## Acceptance criteria

- [ ] With BlueStacks open at 1920x1080, CLI command captures one frame to log path
- [ ] Wrong resolution or no matching window yields non-zero exit and clear message
- [ ] WindowBinder unit-tested with fake window metadata; HostCapture uses fixture in tests
- [ ] Default Window title rule documented after Operator calibration note in README

## Blocked by

Issue for slice 01 (CLI bootstrap and RunConfig)
