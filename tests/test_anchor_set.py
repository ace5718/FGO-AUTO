from pathlib import Path

from fgo_auto.run.anchor_set import merge_anchor_set


def test_override_replaces_script_anchor(tmp_path: Path) -> None:
    script = {"enter_quest": "script/eq.png", "support": "script/sup.png"}
    run = {"enter_quest": "run/eq.png"}
    merged = merge_anchor_set(script, run, base_dir=tmp_path)
    assert merged["enter_quest"] == (tmp_path / "run/eq.png").resolve()
    assert merged["support"] == (tmp_path / "script/sup.png").resolve()


def test_run_adds_new_anchor_name(tmp_path: Path) -> None:
    merged = merge_anchor_set({"a": "1.png"}, {"b": "2.png"}, base_dir=tmp_path)
    assert "a" in merged and "b" in merged
