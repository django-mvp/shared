# ADR 0004 — Python tools run as local pre-commit hooks, not upstream mirrors

**Status:** Accepted (2026-07-21)

## Context

Family repos previously mixed two hook styles: mypy/deptry as `repo: local` hooks running
in the Poetry env, but ruff/black/pyupgrade as upstream pre-commit mirrors with per-repo
`rev:` pins bumped by autoupdate. Consequences: tool versions drifted per repo outside the
shared bundle's control, and `poetry run ruff` didn't work locally because ruff wasn't in
the env (each repo's verify tooling had to special-case it).

## Decision

The family pre-commit template (`templates/pre-commit-config.yaml`) runs **all Python
tools — ruff (lint + format), mypy, deptry — as `repo: local` hooks in the Poetry env**,
with versions supplied by the `mvp-shared[dev]` bundle. **black and pyupgrade are
retired**: `ruff format` is a drop-in black replacement, and ruff's UP rules cover
pyupgrade. The mypy hook sets `require_serial: true` — parallel pre-commit batches race on
the shared `.mypy_cache` and crash on a cold cache (root-caused 2026-07-21).

## Rationale

- One version source: the bundle pins every tool; per-repo `rev:` drift disappears.
- Hook behaviour equals `poetry run <tool>` behaviour equals CI behaviour.
- Fewer tools: one formatter/linter binary instead of three hook environments.

## Consequences

- Downstream repos copy the template and enable ruff's UP rules in `[tool.ruff.lint]`.
- pre-commit.ci can only run the env-independent hooks; the local hooks run in each repo's
  CI Code Quality job (already the family pattern).
- Adding a Python tool to the standard means: add it to the `dev` bundle here, add a local
  hook to the template, propagate.
