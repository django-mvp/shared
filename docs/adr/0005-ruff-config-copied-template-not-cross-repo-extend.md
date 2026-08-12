# ADR 0005 — Ruff configuration ships as a copied template, not a cross-repo `extend`

**Status:** Accepted (2026-08-12)

## Context

Every package in the family carries its own full copy of `[tool.ruff]` in `pyproject.toml`.
The shared bundle pins ruff's *version* (ADR 0004), but not its *configuration*, so the
settings had already drifted: a stray `target-version` in one package that disagreed with
its own `requires-python`, `[tool.ruff.format]` present in only two of five packages, and
ignore lists that had grown from a common six entries to as many as ten with no record of
which additions were deliberate.

The obvious fix — point each package's `[tool.ruff]` at this repo with `extend =
"..."` — does not work. Ruff's `extend` setting only accepts a local filesystem path; it
has no support for a remote reference, and each package is a separate git repository. A
shared config can only be *read* by `extend` once it already exists on disk in the
consuming repo.

## Decision

Add `templates/ruff-shared.toml`, a standalone `ruff.toml`-format file (no `[tool.ruff]`
wrapper) holding the settings genuinely common to the family: the lint rule selection, the
six ignores that were common to every package before drift, the shared `extend-exclude`
list, and the `[format]` settings. Downstream packages copy it to their repo root as
`ruff-shared.toml` — the same copy-and-re-copy discipline already used for
`templates/pre-commit-config.yaml` — and reference it with `extend = "ruff-shared.toml"`
in their own `[tool.ruff]`. A package's own file then holds only its remainder: additional
ignores, additional excludes, per-file carve-outs, and any format keys that differ.

`line-length` and `target-version` are absent from the shared file. Line length defaults
to 88, matching Black; target-version is inferred from each package's own
`requires-python`. Setting either in the shared file would only reintroduce a place for
them to drift.

Reformatting the four packages still on 120 columns, and reconciling each package's
remaining ignore-list entries against the shared six, are separate per-package changes —
each is a large mechanical diff better landed as its own pull request once this base
config exists to land against.

## Rationale

- `extend`'s single-file, override-plus-accumulate merge semantics (a child's `select`
  replaces the parent's; a child's `ignore` accumulates with the parent's as long as the
  child does not also set `select`) is designed for exactly this shared-base-plus-local-
  remainder shape, once the base file is reachable on disk.
- Copying a file downstream and re-copying it on a version bump is not a new mechanism —
  it is the one this repo already uses for the pre-commit template, so there is one
  distribution discipline to remember, not two.
- Keeping `line-length` and `target-version` out of the shared file (rather than pinning
  the family to a value there) matches the standard already adopted in the family's most
  current package: infer, don't restate.

## Consequences

- Downstream packages adopt this by copying `templates/ruff-shared.toml` in and trimming
  their own `[tool.ruff]` down to the remainder, one package per pull request.
- A future shared-config change (e.g. adding a rule to `select`) is one edit here plus one
  re-copy per downstream repo at the next tag bump — the same propagation shape as every
  other part of the family standard (ADR 0002).
- If ruff ever adds native support for a remote `extend` target, this ADR is revisited;
  today's decision is a consequence of `extend` accepting only a local path.
