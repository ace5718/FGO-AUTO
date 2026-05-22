# v1 slice: Quest loop v0 with Battle assist and Stop conditions

GitHub: ace5718/FGO-AUTO#7

## Status

已關閉（main 已實作，pytest 通過）。

## Parent

PRD v1 Screen state and Quest loop.

## What to build

End-to-end Run: enter quest via Quest anchor, deploy with AP check each sortie, Battle assist triggers autoplay UI, wait for Result, increment loop until Loop limit, insufficient AP, or Manual stop. Normal Run end distinct from Run pause.

## Acceptance criteria

- [x] Run completes N Quest loop iterations when Loop limit N configured
- [x] AP insufficient ends with Normal Run end and log reason
- [x] Manual stop from CLI ends Run normally
- [x] Battle assist attempts autoplay control; documented if TW UI differs
- [x] Integration test uses fakes for HostCapture/APReader; no live emulator in CI

## Blocked by

Issues for slices 03 (State catalog) and 04 (Quest anchor)