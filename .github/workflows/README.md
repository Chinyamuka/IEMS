# CI Workflow

One workflow: **`ci.yml`** → pytest on every push + PR to main.

## What it runs

- Checkout → Python 3.14 → install deps → `pytest -q`

## Not yet included (see BUILD_HISTORY.md / Tier 3)

- Postgres service container (currently SQLite only — same as local tests)
- Lint (`ruff`)
- Migration drift check (`flask db upgrade --sql`)
- Render deploy gating (Render auto-deploys on push; it does not wait for CI yet)

## How to add a step

Append to the `steps:` list in `ci.yml`. Test locally first:

    act -j test

(requires [nektos/act](https://github.com/nektos/act))