# MVP Shared

Shared tooling and reusable GitHub Actions workflows for downstream django-mvp repositories.

This repository provides:

- A single shared package for dev and test dependency bundles.
- Reusable CI workflows for build, test matrix, docs deploy, and release.
- Composite actions used by those workflows.
- Pre-commit templates every downstream repository copies, one per package manager.
- A base ruff configuration every downstream repository copies and extends.

## Scope & philosophy

This repository is the single source of the development standard for the django-mvp
packages and any other repository that adopts it: how each one is built, tested, linted,
and released, and which tool versions it does that with. One tagged release here versions
the whole standard.

It deliberately ships no runtime code — the installable package is an empty shell whose
only job is carrying dependency bundles. It is not a Django app, not a general-purpose
actions library, and not a place for repo-specific configuration: anything only one
downstream repository needs belongs in that repository.

When choices collide: reproducibility beats convenience (pin tags, never `main`), one
standard applied identically in every downstream repository beats per-repo flexibility,
and automation is only as trusted as the validation gating it.

## Use In Downstream Projects

This repository exposes shared dependency bundles through optional extras:

- dev
- test

Use a tagged release instead of main so downstream environments are reproducible.

### Poetry

Add both shared extras to a downstream project:

```bash
poetry add --group dev "mvp-shared[dev,test]@git+https://github.com/django-mvp/shared.git@v0.1.0"
```

You can also add it directly in pyproject.toml:

```toml
[tool.poetry.group.dev.dependencies]
mvp-shared = { git = "https://github.com/django-mvp/shared.git", tag = "v0.1.0", extras = ["dev", "test"] }
```

### pip

Install directly from a tag:

```bash
pip install "mvp-shared[dev,test] @ git+https://github.com/django-mvp/shared.git@v0.1.0"
```

### Recommended Update Flow

1. Update and release this shared repo.
2. Bump the tag used by each downstream project.
3. Re-lock dependencies in each downstream project.

## Release Flow

Protected default branches mean version bumps land by PR and tags are cut afterwards —
never pushed together to main. Two workflows implement this; a release costs two actions:
dispatch, then merge.

1. **Prepare Release** (`.github/workflows/prepare-release.yml`, `workflow_dispatch`):
   choose a bump level (patch / minor / major, or an explicit version). It bumps the
   version with Poetry, opens a `CHANGELOG.md` section when one exists, and opens a
   `release/vX.Y.Z` PR. Merging that PR **is** the release decision.
2. **Tag Release** (`.github/workflows/tag-release.yml`, on push to main): notices the
   project version has no matching tag and creates the `vX.Y.Z` tag plus the GitHub
   Release from the merge commit. Dependency-only pyproject changes no-op (tag exists).

Both are also `workflow_call`-reusable so downstream repositories can adopt the same flow
with thin callers.

Token note: these workflows need a personal access token, held as the `RELEASE_TOKEN` org
secret. Prepare Release cannot run without one, because it rewrites files under
`.github/workflows` and GitHub refuses those pushes from `GITHUB_TOKEN`. Two further
limits lift with it: the release PR triggers CI, which it does not when opened by
`GITHUB_TOKEN`, and the created release fires `release`-event workflows.

Downstream callers pass it explicitly, because a reusable workflow sees only the secrets
its caller maps in:

```yaml
    secrets:
      RELEASE_TOKEN: ${{ secrets.RELEASE_TOKEN }}
```

`release-token` was the earlier name for the same secret. It is still honoured so a
repository can repin and rename in separate changes, but it is deprecated, warns when
used, and will be removed.

## Pre-commit Template

There are two templates carrying the hook set every downstream repository runs — ruff
(lint + format), mypy and deptry running as local hooks inside the project environment,
with versions supplied by the `dev` bundle. Copy the one matching the `package-manager`
input the repository passes to the shared workflows:

| Template | For repositories using | Runs tools via | Lockfile hook |
|---|---|---|---|
| `templates/pre-commit-config.yaml` | Poetry | `poetry run` | `poetry-check`, `poetry-lock` |
| `templates/pre-commit-config-uv.yaml` | uv | `uv run` | `uv-lock` |

Copy it to the repository root as `.pre-commit-config.yaml`, replace the
package-directory placeholder, and enable ruff's `UP` rules in `[tool.ruff.lint]` (they
replace pyupgrade; `ruff format` replaces black). The templates' comments explain the
serialised mypy hook and what runs where in CI. A hook added to one is added to the
other.

## Shared Ruff Configuration

`templates/ruff-base.toml` is the base ruff configuration every downstream repository
extends: the shared rule selection, the shared ignore list, and the shared format
settings. Ruff's `extend` option only accepts a local filesystem path, so a package cannot
point at this file across repositories directly — copy it to the repository root as
`ruff-base.toml` (re-copy on each change to this file, the same discipline as the
pre-commit template above), then reference it from the package's own `pyproject.toml`:

```toml
[tool.ruff]
extend = "ruff-base.toml"

[tool.ruff.lint]
extend-ignore = []  # package-specific additions, if any

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101"]  # asserts are the point of a test
```

This split is the standard, and the filename is part of it: the base config under a name
ruff does **not** auto-discover, and the package's own settings in `pyproject.toml`. Do not
rename the base file to `ruff.toml` or `.ruff.toml`. Ruff discovers both, and when either is
present in a directory it uses that file *instead of* the `[tool.ruff]` section in
`pyproject.toml` rather than merging the two, so the package's `extend`, per-file-ignores
and format settings would quietly stop applying while lint carried on reporting success.
Ruff's documentation gives the order: `.ruff.toml` takes precedence over `ruff.toml`, which
takes precedence over `pyproject.toml`. Confirmed against ruff 0.15.22.

Once extending, a package's own `[tool.ruff]` holds only its remainder: additional ignored
rules under `[tool.ruff.lint] extend-ignore`, additional excluded paths under
`extend-exclude`, per-file carve-outs for tests and examples, and any
`[tool.ruff.format]` keys that differ from the shared ones — never a restatement of the
shared rule set. `line-length` and `target-version` stay unset in both files: line length
defaults to 88 (matching Black), and target-version is inferred from the package's own
`requires-python`, so leaving both alone is what keeps them from drifting.

## Reusable Workflows

Downstream repositories can call these workflows directly from their own workflow files.

### Choosing a package manager

`build.yml`, `tests.yml` and `docs.yml` each take a `package-manager` input that selects
how the environment is set up. It defaults to `poetry`, so a caller that does not set it
keeps working exactly as before.

| `package-manager` | Environment built by | Extra arguments input |
|---|---|---|
| `poetry` (default) | `poetry install` against `poetry.lock` | `poetry-install-args` |
| `uv` | `uv sync --locked` against `uv.lock` | `uv-sync-args` |

A repository sets this once, when its `pyproject.toml` and lockfile move to uv. Both
tracks install into `.venv` and put it on `PATH`, so everything the workflows run after
setup — `pytest`, `pre-commit`, `sphinx-build` — is identical on either.

Two checks differ, because the tools do:

- **Lockfile consistency.** On the poetry track `build.yml` runs `poetry check --lock` as
  its own step. On the uv track the setup action syncs with `--locked`, which already
  fails on a stale lockfile, so the separate step is skipped rather than missing.
- **Package metadata.** `poetry check` validates the source `pyproject.toml`. uv has no
  equivalent, so the uv track runs `twine check` over the built wheel and sdist instead,
  which reads the metadata the way PyPI's upload endpoint does.

A repository moving to uv also changes build backend, since `poetry-core` is Poetry's.
One thing to set explicitly when it does:

```toml
[tool.hatch.build.targets.sdist]
include = ["<package_dir>", "README.md", "LICENSE"]
exclude = [".gitignore"]
```

`poetry-core` published only the package directory, the readme and the licence. Hatchling
defaults to publishing the whole working tree, so without this the source distribution
that reaches PyPI carries the test suite, the demonstration project, documentation, CI
configuration and anything else in the repository. The wheel is unaffected — it is built
from the declared packages either way.

### Build

Reusable workflow: .github/workflows/build.yml

Required inputs:

- source-dir

Optional inputs:

- python-version (default: 3.13)
- package-manager (default: poetry)
- uv-sync-args (default: empty)

Example caller workflow:

```yaml
name: Build

on:
  push:
    branches: [main]
  pull_request:

jobs:
  build:
    uses: django-mvp/shared/.github/workflows/build.yml@v0.1.0
    with:
      source-dir: mvp
      python-version: "3.13"
```

### Tests

Reusable workflow: .github/workflows/tests.yml

Required inputs:

- coverage-package

Optional inputs:

- python-versions (default: ["3.12", "3.13"])
- django-versions (default: ["5.2", "6.0"])
- package-manager (default: poetry)
- poetry-install-args (default: --with test)
- uv-sync-args (default: empty)
- coverage-python-version (default: 3.13)
- coverage-django-version (default: 5.2)
- install-playwright (default: false)

Example caller workflow:

```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:

jobs:
  tests:
    uses: django-mvp/shared/.github/workflows/tests.yml@v0.1.0
    secrets: inherit
    with:
      coverage-package: mvp
      python-versions: '["3.12", "3.13"]'
      django-versions: '["5.2", "6.0"]'
      poetry-install-args: "--with test"
```

### Docs Deployment

Reusable workflow: .github/workflows/docs.yml

Optional inputs:

- python-version (default: 3.13)
- package-manager (default: poetry)
- uv-sync-args (default: empty)

Example caller workflow:

```yaml
name: Docs

on:
  push:
    branches: [main]

jobs:
  docs:
    uses: django-mvp/shared/.github/workflows/docs.yml@v0.1.0
    with:
      python-version: "3.13"
```

### Release

Reusable workflow: .github/workflows/release.yml

Behavior:

- Looks for a version tag (v*) on the triggering commit.
- Creates a GitHub Release only when a matching tag exists.

Outputs:

- tag

Example caller workflow:

```yaml
name: Release

on:
  workflow_run:
    workflows: ["Build"]
    types: [completed]

jobs:
  release:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    uses: django-mvp/shared/.github/workflows/release.yml@v0.1.0
    secrets: inherit
```

## Composite Actions

The reusable workflows above call these to build the project environment. A downstream
repository normally reaches them through a workflow rather than directly, but both are
usable on their own.

Each one installs the project and its dependencies into `.venv`, then exports three
things so the steps that follow do not need to know which was used:

- `.venv/bin` on `PATH`, so tools are invoked bare (`pytest`, not `poetry run pytest`)
- `VIRTUAL_ENV`
- `PYTHON_INSTALL_CMD`, the command for installing an extra package into the environment

### setup-poetry

Composite action: .github/actions/setup-poetry

Installs Python via `actions/setup-python`, then Poetry, and runs `poetry install`. Caches
`.venv` directly, keyed on the resolved interpreter patch release (see ADR 0008).

Optional inputs:

- python-version (default: 3.13)
- poetry-version (default: 2.3.2)
- poetry-install-args (default: empty)
- cache-key-suffix (default: empty)

### setup-uv

Composite action: .github/actions/setup-uv

Installs uv via `astral-sh/setup-uv`, which also provides the interpreter, then runs
`uv sync --locked`. `--locked` fails the job on a lockfile that is out of date with
`pyproject.toml` rather than quietly re-resolving it, matching how `poetry install`
refuses an inconsistent lock.

Caches uv's global package cache rather than the resolved environment. The poetry action
has to cache `.venv` and key it on the interpreter's patch release, because an in-project
virtual environment stores an absolute interpreter path and stops working when the runner
image rolls forward. Caching downloads instead avoids that failure entirely: the
environment is always built fresh, from cached wheels.

Optional inputs:

- python-version (default: 3.13)
- uv-version (default: 0.11.19)
- uv-sync-args (default: empty)
- cache-key-suffix (default: empty)

`cache-key-suffix` exists for the same reason on both: two jobs in one workflow run that
resolve to the same inputs otherwise race to write the same cache entry.

## Version Pinning Recommendation

When referencing reusable workflows from downstream projects, pin to a tag instead of main:

- Recommended: @v0.1.0
- Avoid for production stability: @main
