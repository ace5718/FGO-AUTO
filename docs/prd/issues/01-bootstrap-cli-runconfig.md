# v1 slice: Python CLI bootstrap and RunConfig loading

GitHub: ace5718/FGO-AUTO#3

## Status

已關閉（main 已實作，pytest 通過）。

## Parent

Published as child of PRD issue (v1 Screen state and Quest loop).

## What to build

Tracer bullet: Python 3.11+ package with a CLI entrypoint and RunConfig loading from YAML/JSON. Operator can run `--help`, load a sample Run config (Script id, Loop limit, Window title rule, anchor paths, recognition retry budget default 5), and see structured logs. No capture yet.

## Acceptance criteria

- [x] `pyproject.toml` / pytest run green in CI-friendly way (fixtures only)
- [x] CLI prints version and loads RunConfig; invalid config fails with clear error
- [x] RunConfig fields: script, loop_limit, window_title_rule, anchors map, recognition_retries
- [x] README section: how to create a minimal Run config

## Blocked by

None - can start immediately