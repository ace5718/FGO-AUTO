"""Move run_config into fgo_auto.run package to fix Pylance run/run_config ambiguity."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "fgo_auto"
OLD = SRC / "run_config.py"
NEW = SRC / "run" / "run_config.py"

IMPORT_OLD = "from fgo_auto.run_config import"
IMPORT_NEW = "from fgo_auto.run.run_config import"


def main() -> None:
    content = OLD.read_text(encoding="utf-8")
    NEW.write_text(content, encoding="utf-8", newline="\n")
    OLD.unlink()

    for path in list(ROOT.rglob("*.py")):
        if path == NEW or "venv" in path.parts or path.name == "migrate_run_config.py":
            continue
        text = path.read_text(encoding="utf-8")
        if IMPORT_OLD in text:
            path.write_text(text.replace(IMPORT_OLD, IMPORT_NEW), encoding="utf-8", newline="\n")
            print("updated", path.relative_to(ROOT))

    write_script = ROOT / "scripts" / "write_run_config.py"
    if write_script.is_file():
        t = write_script.read_text(encoding="utf-8")
        t = t.replace(' / "run_config.py"', ' / "run" / "run_config.py"')
        write_script.write_text(t, encoding="utf-8", newline="\n")

    print("migrated to", NEW)


if __name__ == "__main__":
    main()
