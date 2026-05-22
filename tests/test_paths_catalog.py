from fgo_auto.services.paths import catalog_dir, catalog_dir_for_preset, repo_root


def test_catalog_dir_for_preset_fallback() -> None:
    path = catalog_dir_for_preset(1920, 1080)
    assert path.is_dir()
    assert path == catalog_dir() or (repo_root() / "tests" / "fixtures" / "catalog_v02") == path
