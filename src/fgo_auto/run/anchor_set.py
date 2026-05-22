from __future__ import annotations

from pathlib import Path


def merge_anchor_set(
    script_anchors: dict[str, str],
    run_overrides: dict[str, str],
    *,
    base_dir: Path | None = None,
) -> dict[str, Path]:
    """Merge Script anchors with Run anchor overrides by name."""
    merged = {name: Path(path) for name, path in script_anchors.items()}
    for name, path in run_overrides.items():
        merged[name] = Path(path)

    if base_dir is not None:
        resolved: dict[str, Path] = {}
        for name, path in merged.items():
            resolved[name] = path if path.is_absolute() else (base_dir / path).resolve()
        return resolved
    return merged
