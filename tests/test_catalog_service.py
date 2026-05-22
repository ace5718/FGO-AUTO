from pathlib import Path

import pytest

from fgo_auto.services.catalog_service import count_templates, save_state_template


def test_save_state_template(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from fgo_auto.services import catalog_service as cs

    import fgo_auto.services.paths as paths

    data = tmp_path / "data"
    monkeypatch.setattr(cs, "data_root", lambda: data)
    monkeypatch.setattr(paths, "data_root", lambda: data)
    src = tmp_path / "frame.png"
    src.write_bytes(b"\x89PNG\r\n\x1a\n")
    dest = save_state_template((961, 573), "main", src)
    assert dest.is_file()
    assert count_templates((961, 573)) == 1
