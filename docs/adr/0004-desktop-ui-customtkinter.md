# ADR-0004: Desktop UI with CustomTkinter

## Status

Accepted

## Context

Operators need a local desktop UI to control Runs, edit Run config, preview captures, and read logs without relying on a browser or cloud service. Phase 2 will add anchor/catalog visual editing on top of the same capture pipeline.

## Decision

- Ship **FGO-AUTO Desktop app** as a **CustomTkinter** window (`fgo-auto-gui` entry point).
- Share automation logic with the CLI via a **service layer** (`ConfigService`, `CaptureService`, `RunService`, `WindowService`).
- Store operator data under **Local data root** (`data/profiles/`, `data/anchors/`, `logs/`); nothing leaves the machine.
- Run Quest loops on a **daemon thread**; UI updates only on the main thread via a **queue** of events.
- CI does not run GUI tests; service-layer tests stay headless.

## Consequences

- Optional install: `pip install -e ".[dev,windows,gui]"`.
- Pillow used for preview thumbnails; full frames still written under `logs/`.
- Phase 2 can add `SelectionCanvas` and catalog management without changing the service contracts (`save_anchor_crop`, `list_catalog_states` stubs exist).

## References

- GitHub issue #9 (MVP), #10 (Phase 2 visual editor)
- Plan: Local data root layout in `data/profiles/default/`
