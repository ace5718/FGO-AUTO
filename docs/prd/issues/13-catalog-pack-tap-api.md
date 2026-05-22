# v0.2 slice: Catalog per display preset + normalized tap API

GitHub: ace5718/FGO-AUTO#13

## Status

開啟（已發布至 GitHub）

## Parent

PRD v0.2.0 (#11).

## What to build

Resolve catalog directory from `display_preset` (e.g. `data/catalog/1920x1080/`). Expose `tap_normalized` on script/host layer. Migrate `services/paths.catalog_dir()` to accept preset. Fixture tests at two sizes optional.

## Acceptance criteria

- [ ] `StateCatalog.from_directory` loads from preset pack path
- [ ] `tap_normalized(frame, x, y)` clicks correct pixels on win32
- [ ] Fallback to repo `catalog/` or fixtures for dev when pack missing
- [ ] pytest without emulator

## Blocked by

- #12 (12-adr-display-preset.md)