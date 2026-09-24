# ADR 0009 — uv replaces Poetry, and v0.5.0 supports uv only

**Status:** Accepted (2026-09-24)

## Context

Up to v0.4.x everything here assumed Poetry: the reusable workflows installed it through a
`setup-poetry` composite action and ran every tool through `poetry run`, the pre-commit
template's hooks did the same, and the release workflows bumped the version with
`poetry version`.

The repositories that call these workflows are moving to uv. A first version of that move
added uv as a second, opt-in track beside Poetry, selected by a `package-manager` input.
Keeping both would mean two setup paths in every workflow, two pre-commit templates kept
in step by hand, and every future change tested twice, for as long as any repository stayed
behind.

## Decision

v0.5.0 supports uv only. Poetry support is removed from the workflows, the actions, the
template and this repository's own packaging. A repository still on Poetry stays pinned to
v0.4.x until it moves. The README's "Moving from Poetry" section lists what moving takes.

The workflows call `astral-sh/setup-uv` directly rather than through an action of our own.
Everything a wrapper would add is one `uv sync --locked` step. A pin inside one of this
repository's own actions is also one that Dependabot never updated. The actions that
existed here sat a major version behind the workflows until Dependabot was pointed at them
in the same change.

Hatchling is the build backend, here and in every repository that moves. `uv_build` only
builds pure-Python packages and has no per-format file includes, which at least one
downstream package needs.

## Consequences

- ADR 0006 no longer applies. No workflow here calls one of this repository's own actions
  by `owner/repo/path@ref` any more, so there is nothing to re-pin at release, and the
  re-pin steps are gone from Prepare Release.
- ADR 0008 no longer applies. uv caches downloaded packages rather than `.venv`, so a
  runner-image roll can no longer leave a restored environment pointing at a missing
  interpreter. The two scripts that guarded the old cache (key uniqueness and interpreter
  pinning) are removed with it.
- ADR 0004's decision stands. The pre-commit tools still run as local hooks from the shared
  bundle, now through `uv run`.
- `uv.lock` records the project's own version. Every version bump goes through
  `uv version`, which updates both files. The release workflows do this, and editing
  `pyproject.toml` alone leaves every `uv sync --locked` failing.
- The Poetry-to-uv move is a breaking change in a minor release. Article VIII is amended to
  allow that before 1.0, as long as the release carries migration notes.
