# v1 slice: State catalog v0 and Run pause on recognition failure

## Parent

PRD v1 Screen state and Quest loop.

## What to build

StateCatalog detects Unknown, Main, Terminal, Battle, Result from frames. RunController applies Recognition retry (default 5) then Run pause with log plus screenshot on failure. CLI command runs detect-only loop printing Screen state transitions.

## Acceptance criteria

- [ ] Fixture images classify to expected Screen state per catalog entry
- [ ] Unknown used when confidence below threshold
- [ ] After retry budget exhausted, Run enters Run pause (not Normal Run end)
- [ ] pytest covers StateCatalog and RunController pause path without emulator

## Blocked by

Issue for slice 02 (Host capture)
