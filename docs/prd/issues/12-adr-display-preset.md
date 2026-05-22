# v0.2 slice: ADR-0005 configurable Display preset and normalized coordinates

GitHub: ace5718/FGO-AUTO#12

## Status

開啟（已發布至 GitHub）

## Parent

PRD v0.2.0 (#11).

## What to build

Document and implement the resolution contract: any `[width, height]` preset matching the BlueStacks window; normalized tap coords; update capture error messages and CONTEXT. Amend references from ADR-0001-only wording in README where needed.

## Acceptance criteria

- [ ] `docs/adr/0005-configurable-display-preset.md` accepted
- [ ] CONTEXT.md updated; Display preset pack term defined
- [ ] Capture mismatch message mentions Operator-adjustable preset
- [ ] Helper to convert normalized (x,y) to pixel coords with tests

## Blocked by

None - can start immediately