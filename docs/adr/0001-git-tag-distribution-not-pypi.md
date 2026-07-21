# ADR 0001 — Distribute by git tag, not PyPI

**Status:** Accepted (2026-07-21)

## Context

The `mvp-shared` meta-package must reach downstream repos reproducibly. Options: publish
to PyPI, or have downstream repos install from a git tag.

## Decision

Distribution is by **git dependency pinned to a `vX.Y.Z` tag**. No PyPI publication.

## Rationale

- Every consumer is a Poetry-managed repo in the same family; git dependencies with a tag
  are fully reproducible there and need no publishing pipeline, credentials, or index
  metadata.
- One tag then versions the *entire* standard — workflow calls (`@vX.Y.Z`) and the
  dependency bundles reference the same ref, so "which standard is this repo on" has a
  single answer.
- PyPI adds a public surface (name squatting, metadata upkeep, README rendering) with no
  consumer that needs it.

## Consequences

- The README's install instructions always show the tag form; `@main` is documented as
  unsuitable for downstream use.
- If a consumer ever appears that cannot install git dependencies, this ADR is revisited.
