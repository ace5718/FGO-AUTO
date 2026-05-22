# State catalog templates (TW / 1920x1080)

Place PNG templates under subfolders named for each Screen state:

- `unknown/` (optional)
- `main/`
- `terminal/`
- `battle/`
- `result/`

CI and local tests use `tests/fixtures/catalog/`. For live Runs, capture snippets from your BlueStacks window at 1920x1080 and add them here (or pass `--catalog-dir`).

Optional battle assist template: pass `--battle-assist-template` to `fgo-auto run`.
