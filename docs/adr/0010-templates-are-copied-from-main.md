# ADR 0010 — Templates are copied from main, not from a release tag

**Status:** Accepted (2026-10-28)

## Context

Downstream repositories take three kinds of thing from this repository:

- the reusable workflows, called by reference,
- the `mvp-shared` dependency bundles, installed from git,
- the files under `templates/` (`ruff-base.toml` and `pre-commit-config.yaml`), copied in.

All three were tied to one release tag. A repository copied the templates as they stood at the tag it pinned, and its copy was compared against that tag. A change to a template therefore reached no repository until a release was cut, however small the change. The docstring rules added to `ruff-base.toml` sat on `main` unreleased, while the packages that copied it at v0.6.0 checked no docstrings at all.

## Decision

Templates are copied from `main`. A downstream repository's copy is compared against the template on `main`, not against the tag it pins.

Workflows and the dependency bundles stay pinned to a release tag. They are executable, and a caller needs the version it runs to stay put until it chooses to move.

## Consequences

- A template change reaches the packages as soon as it merges here, without a release. Each package picks it up by re-copying the file.
- A repository's copy can fall behind `main` between re-copies. The comparison reports that as drift to fix, not as a broken build.
- A template change that depends on something only a release carries still waits for that release. For example, a pre-commit hook that runs a tool new to the `mvp-shared[dev]` bundle cannot be copied until the bundle that ships the tool is tagged.
- ADR 0005's copy-and-re-copy discipline is unchanged. Only the source of the copy moves from the tag to `main`.
