# ADR-0005: Configurable Display preset and normalized tap coordinates

## Status

Accepted (v0.2.0)

## Context

ADR-0001 required exactly 1920×1080. Operators often run BlueStacks at other sizes (e.g. 1632×933). v0.2.0 adds full navigation and battle scripting; anchors and catalog must work per actual window size.

## Decision

1. **RunConfig.display_preset** remains `[width, height]` but means “expected capture size” for any matching BlueStacks window, not only 1920×1080.
2. **HostCapture** rejects runs when frame size does not match preset (unchanged check, clearer messaging).
3. **Catalog and anchors** are stored per preset under `data/catalog/<width>x<height>/` and `data/anchors/` (flat or subdirs by preset).
4. **Tap targets** in scripts and profiles may use **normalized coordinates** `(x, y)` in `[0, 1]`, multiplied by current frame width/height at runtime.
5. **Image templates** are not auto-scaled; each preset pack needs its own PNG set.

## Consequences

- Operators calibrate once per resolution they use.
- ADR-0001 remains historical; README points to ADR-0005 for v0.2+.
- Tests use fixture frames at declared preset sizes.

## References

- v0.2 PRD: `docs/prd/0002-v0.2-full-quest-and-battle-script.md`
- GitHub #12
