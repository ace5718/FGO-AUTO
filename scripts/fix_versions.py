from pathlib import Path


def read_text(p: Path) -> str:
    b = p.read_bytes()
    if len(b) >= 2 and b[1] == 0:
        return b.decode("utf-16-le")
    return b.decode("utf-8")


def write_utf8(p: Path, t: str) -> None:
    p.write_text(t, encoding="utf-8")


def main() -> None:
    pp = Path("pyproject.toml")
    t = read_text(pp)
    t = t.replace('version = "0.1.0"', 'version = "0.2.0"')
    write_utf8(pp, t)

    tc = Path("tests/test_cli.py")
    t = read_text(tc)
    old = '    assert "0.1.0" in result.stdout'
    new = "    from fgo_auto import __version__\n\n    assert __version__ in result.stdout"
    if old in t:
        t = t.replace(old, new)
    write_utf8(tc, t)

    rm = Path("README.md")
    t = read_text(rm)
    t = t.replace("**Version:** `0.1.0`", "**Version:** `0.2.0`")
    write_utf8(rm, t)

    cl = Path("CHANGELOG.md")
    t = read_text(cl)
    if "## [0.2.0]" not in t:
        block = """## [0.2.0] - 2026-05-22

### Added
- Quest profile (script_version v2), NavigationEngine, BattleScriptEngine, ScriptEngineV2
- catalog_dir_for_preset, tap_normalized, CLI --quest-profile
- GUI: script version / quest profile; catalog list; minimal anchor crop

### Changed
- Default script_version remains v0 for v0.1 compatibility

"""
        if t.startswith("# Changelog"):
            lines = t.splitlines()
            t = lines[0] + "\n\n" + block + "\n".join(lines[1:])
        else:
            t = "# Changelog\n\n" + block + t
    write_utf8(cl, t)
    print("done")


if __name__ == "__main__":
    main()
