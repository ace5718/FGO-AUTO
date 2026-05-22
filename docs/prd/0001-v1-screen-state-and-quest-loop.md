# PRD: v1 Screen state skeleton and Quest loop (TW / BlueStacks 5)

## Problem Statement

Operators who play TW FGO on BlueStacks 5 want to repeat a quest without manually tapping through the same UI every time. They need a trustworthy automation helper that recognizes where the game is (Screen state), can find a quest entry from images they provide (Quest anchor), and stops safely when AP runs out, a Loop limit is reached, or recognition fails.

## Solution

FGO-AUTO v1 delivers a Python CLI that runs a Run against a bound BlueStacks window at a fixed Display preset (1920x1080). The Script drives a small State catalog, uses Quest anchors (Script defaults plus Run overrides) to enter a quest, applies Battle assist during battle, and completes Quest loop iterations until a Stop condition fires or the Run enters Run pause after Recognition failure.

## User Stories

1. As an Operator, I want to start a Run from the CLI with a Run config, so that I can automate without a GUI.
2. As an Operator, I want the tool to bind exactly one BlueStacks game window via a Window title rule, so that capture targets the correct instance.
3. As an Operator, I want the Run to refuse to start if the game window is not 1920x1080, so that anchors stay reliable.
4. As an Operator, I want to supply Quest anchor images, so that I can target any quest entry without hard-coded quest IDs.
5. As an Operator, I want Script anchors with optional Run anchor overrides, so that I can reuse defaults and override for one-off farms.
6. As an Operator, I want the Script to log Screen state transitions, so that I can diagnose stuck flows.
7. As an Operator, I want built-in Screen states (Main, Terminal, Battle, Result, Unknown), so that the state machine has stable names.
8. As an Operator, I want Recognition retry before Run pause, so that short animations do not false-trigger failure.
9. As an Operator, I want Run pause with logs and a screenshot on Recognition failure, so that I can fix the UI and resume later.
10. As an Operator, I want Battle assist to trigger in-game autoplay during Battle, so that Combat strategy is out of scope for v1.
11. As an Operator, I want AP check before each deploy or sortie, so that the Run ends normally when AP is insufficient.
12. As an Operator, I want a configurable Loop limit, so that the Run stops after N Quest loop iterations.
13. As an Operator, I want Manual stop from the CLI, so that I can end a Run early.
14. As an Operator, I want Normal Run end distinct from Run pause, so that outcomes are unambiguous in logs.
15. As an Operator, I want one Quest anchor match-and-tap in v1, while the Anchor set model allows more later.
16. As a maintainer, I want deep modules tested with image fixtures, so that refactors stay safe.

## Implementation Decisions

### Milestones

- M1: Host capture, Window binding, Display preset check, logging, CLI shell
- M2: State catalog v0 (Unknown, Main, Terminal, Battle, Result), Recognition retry, Run pause
- M3: Anchor set merge, single Quest anchor match and click
- M4: Quest loop v0 with Battle assist, AP check, Loop limit, Manual stop

### Deep modules

| Module | Responsibility |
|--------|----------------|
| HostCapture | Bind window, verify Display preset, return frames |
| WindowBinder | Window title rule; later Window pick |
| ImageMatch | Template match anchors on a Frame |
| StateCatalog | Frame to built-in Screen state |
| RunController | Run lifecycle, Normal Run end, Run pause, Manual stop |
| ScriptEngine | State machine transitions, Battle assist, Quest loop |
| AnchorSet | Merge Script anchors and Run overrides by name |
| APReader | Heuristic insufficient AP before deploy |
| RunConfig | Load CLI and YAML or JSON |

### ADRs

- 0001 fixed Display preset 1920x1080
- 0002 Python 3.11+
- 0003 Window title rule; Window pick follow-up

### Defaults

- Recognition retry budget: 5
- Display preset: 1920x1080

## Testing Decisions

- pytest with PNG frame fixtures; no emulator in CI
- Prioritize tests: ImageMatch, StateCatalog, AnchorSet, RunController
- Test observable outputs (state, match coordinates, events), not internals

## Out of Scope

- Combat strategy, desktop GUI, multi-resolution scaling, generic popup recovery
- Window pick and Custom Screen states in v1 (follow-up slices)
- Multiple Quest anchor actions in v1 (model only)
- Direct device control outside BlueStacks window

## Further Notes

- Terminology: CONTEXT.md
- Tracer-bullet child issues: docs/prd/issues/
- Publish: scripts/publish-prd-issues.ps1
