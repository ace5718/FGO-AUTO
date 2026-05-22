# v1 slice: Anchor set merge and single Quest anchor tap

## Parent

PRD v1 Screen state and Quest loop.

## What to build

AnchorSet merges Script anchors with Run anchor overrides by name. ImageMatch finds one Quest anchor on current frame and ScriptEngine issues click at match center. CLI subcommand or Run step: given anchor name, tap once and log match score.

## Acceptance criteria

- [ ] Override replaces Script anchor for same name; additional names append
- [ ] Fixture frame plus anchor PNG yields expected coordinates in test
- [ ] No match logs failure without silent continue
- [ ] Works at 1920x1080 only (per ADR-0001)

## Blocked by

Issue for slice 02 (Host capture)
