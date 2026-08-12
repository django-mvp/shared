# ADR 0006 — Pin the internal setup-poetry reference to this repo's own release tag

**Status:** Accepted (2026-08-12)

## Context

`build.yml` and `tests.yml` are reusable workflows consumed by downstream repos as
`django-mvp/shared/.github/workflows/build.yml@vX.Y.Z` (ADR 0001: one tag versions the
whole standard). Inside those workflows, the `setup-poetry` composite action was referenced
as `django-mvp/shared/.github/actions/setup-poetry@main`. A reusable workflow's `uses:`
step for an action in another repository cannot use a local `./` path — that resolves
against the *calling* repository's checkout, not this one — so the qualified
`owner/repo/path@ref` form is required regardless. The bug was the `@ref` chosen: `@main`
floats. A downstream repo pinned to `build.yml@v0.2.0` still picked up whatever
`setup-poetry` looked like on `main` at the moment its job ran, so a commit here could
change every onboarded repo's environment setup without any of them changing a line —
exactly what the pinned-tag policy exists to prevent (django-mvp/shared#24).

The obstacle to just pinning it: the tag a release produces does not exist at the moment
the release commit is written, so a self-reference to that tag looks unresolvable when
read as a diff.

## Decision

The internal reference is pinned to **this repo's own current release tag**, and
`prepare-release.yml`'s version-bump step **re-pins it to the version being released** in
the same commit that bumps `pyproject.toml`. The sequencing works because the reference is
only ever *read* by a caller that has already resolved this repository at that tag — by
the time anyone can fetch `build.yml@vX.Y.Z`, `vX.Y.Z` exists, and the `setup-poetry@vX.Y.Z`
reference inside it resolves against a tag that, by definition, already exists.
`Tag Release` cuts the tag from the exact commit `Prepare Release` produced, so the
self-reference and the tag are written together and always agree.

This repository's own CI does not need the same treatment: `validate.yml` calls
`setup-poetry` via a local path (`./.github/actions/setup-poetry`), which is valid because
`validate.yml` is never consumed cross-repo — it only ever runs against this repo's own
checkout.

## Consequences

- Every future release PR carries a mechanical diff in `build.yml`/`tests.yml` re-pinning
  the tag; that diff is expected and needs no manual edit.
- Between merging a release PR and `Tag Release` actually cutting the tag, `main`
  transiently references a tag that does not exist yet. Nothing consumes `build.yml`/
  `tests.yml` at `@main` for a real build during that window, so this is inert.
- If a caller ever needs an unreleased `setup-poetry` change ahead of a tag, that is a
  deliberate `@main` reference taken on knowingly for that one case, not the default.
