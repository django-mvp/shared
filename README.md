# MVP Shared

Shared tooling and reusable GitHub Actions workflows for downstream django-mvp repositories.

This repository provides:

- A single shared package for dev and test dependency bundles.
- Reusable CI workflows for build, test matrix, docs deploy, and release.
- Composite actions used by those workflows.
- A pre-commit template every downstream repository copies.
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

From v0.5.0 the workflows, the pre-commit template and the release flow here all assume
the downstream repository is managed with [uv](https://docs.astral.sh/uv/): a
`pyproject.toml` with standard `[project]` metadata, a committed `uv.lock`, and uv
commands wherever a tool runs. A repository still on Poetry stays pinned to v0.4.x. See
[Moving from Poetry](#moving-from-poetry) for what changes when it moves.

### uv

Add both shared extras as a development dependency group, pinned to a tag:

```toml
[dependency-groups]
dev = ["mvp-shared[dev,test]"]

[tool.uv.sources]
mvp-shared = { git = "https://github.com/django-mvp/shared.git", tag = "v0.5.0" }
```

`uv sync` installs the `dev` group by default, so the whole toolchain arrives with it.

### pip

Install directly from a tag:

```bash
pip install "mvp-shared[dev,test] @ git+https://github.com/django-mvp/shared.git@v0.5.0"
```

### Recommended Update Flow

1. Update and release this shared repo.
2. Bump the tag in each downstream project's `[tool.uv.sources]` and its workflow callers.
3. Run `uv lock` in each downstream project and commit `uv.lock`.

### Moving from Poetry

v0.5.0 removed Poetry support from everything here. A repository moving up from v0.4.x
makes these changes in one pull request, because the workflows it calls at v0.5.0 expect
all of them:

- **`pyproject.toml`.** Move any remaining `[tool.poetry]` metadata into `[project]`, with
  a static `version`. Turn `[tool.poetry.group.<name>.dependencies]` into
  `[dependency-groups]`, and git or path dependencies into `[tool.uv.sources]`.
  `[tool.poetry.scripts]` becomes `[project.scripts]` and `[tool.poetry.plugins]` becomes
  `[project.entry-points]`.
- **Build backend.** `poetry-core` goes. Use hatchling:

  ```toml
  [build-system]
  requires = ["hatchling"]
  build-backend = "hatchling.build"

  [tool.hatch.build.targets.wheel]
  packages = ["<package_dir>"]

  [tool.hatch.build.targets.sdist]
  include = ["<package_dir>", "README.md", "LICENSE"]
  ```

  Set the sdist `include`. `poetry-core` published only the package directory, the readme
  and the licence. Hatchling defaults to publishing the whole working tree, so without it
  the source distribution that reaches PyPI carries the test suite, any demonstration
  project, documentation and CI configuration. The wheel is built from the declared
  packages either way. Hatchling always adds the repository's `.gitignore` to the source
  distribution, so that a build from it leaves out the same files, and no setting removes
  it.
- **Lockfile.** Delete `poetry.lock`, run `uv lock`, commit `uv.lock`. Expect some
  dependency versions to move: uv resolves afresh.
- **Workflow callers.** Repin to v0.5.0. Remove `poetry-install-args`, and pass
  `uv-sync-args` only if the repository needs something beyond the default groups.
- **Pre-commit.** Re-copy `templates/pre-commit-config.yaml`. Its hooks run through
  `uv run`, and `uv-lock` replaces `poetry-check` and `poetry-lock`.
- **Dependabot.** Change the Python entry's `package-ecosystem` from `pip` to `uv`, so
  updates rewrite `uv.lock`.
- **Versioning.** Bump the version with `uv version`, never by editing `pyproject.toml`
  alone. `uv.lock` records the project's own version, and a lockfile left behind makes
  every `uv sync --locked` fail. The release workflows here already do this.

## Release Flow

Protected default branches mean version bumps land by PR and tags are cut afterwards —
never pushed together to main. Two workflows implement this; a release costs two actions:
dispatch, then merge.

1. **Prepare Release** (`.github/workflows/prepare-release.yml`, `workflow_dispatch`):
   choose a bump level (patch / minor / major, or an explicit version). It bumps the
   version with `uv version`, which updates `pyproject.toml` and `uv.lock` together, opens a
   `CHANGELOG.md` section when one exists, and opens a `release/vX.Y.Z` PR. Merging that PR **is** the release decision.
2. **Tag Release** (`.github/workflows/tag-release.yml`, on push to main): notices the
   project version has no matching tag and creates the `vX.Y.Z` tag plus the GitHub
   Release from the merge commit. Dependency-only pyproject changes no-op (tag exists).

Both are also `workflow_call`-reusable so downstream repositories can adopt the same flow
with thin callers.

Token note: these workflows need a personal access token, held as the `RELEASE_TOKEN` org
secret. Prepare Release refuses to run without one, because a release PR opened by
`GITHUB_TOKEN` triggers no CI, so its required checks never report and it can never merge.
The token also lets the created release fire `release`-event workflows.

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

`templates/pre-commit-config.yaml` is the hook set every downstream repository runs: ruff
(lint + format), mypy, and deptry running as local hooks through `uv run`, with versions
supplied by the `dev` bundle, plus `uv-lock` to keep `uv.lock` in step with
`pyproject.toml`. Copy it to the repository root as `.pre-commit-config.yaml`, replace the
package-directory placeholder, and enable ruff's `UP` rules in `[tool.ruff.lint]` (they
replace pyupgrade; `ruff format` replaces black). The template's comments explain the
serialised mypy hook and what runs where in CI.

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

### How the workflows run

`build.yml`, `tests.yml` and `docs.yml` install uv with
[`astral-sh/setup-uv`](https://github.com/astral-sh/setup-uv), which also provides the
Python interpreter, then build the environment with `uv sync --locked`. `--locked` fails
the job when `uv.lock` is out of date with `pyproject.toml`, rather than re-resolving and
testing whatever that produces. That sync is the lockfile consistency check. Every tool
after it runs through `uv run` against the environment as synced.

The uv version is not pinned here. `setup-uv` uses the repository's
[`required-version`](https://docs.astral.sh/uv/reference/settings/#required-version) when
it sets one, and the latest release otherwise.

Package metadata is checked with `twine check` over the built wheel and sdist, which reads
it the way PyPI's upload endpoint does.

### Build

Reusable workflow: .github/workflows/build.yml

Required inputs:

- source-dir

Optional inputs:

- python-version (default: 3.13)
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
    uses: django-mvp/shared/.github/workflows/build.yml@v0.5.0
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
- uv-sync-args (default: empty)
- coverage-python-version (default: 3.13)
- coverage-django-version (default: 5.2)
- install-playwright (default: false)

Each matrix leg installs the latest patch release of its Django series over the locked
environment and fails if the Django it then imports is not that series, so a leg labelled
6.0 cannot quietly run on 6.1.

Example caller workflow:

```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:

jobs:
  tests:
    uses: django-mvp/shared/.github/workflows/tests.yml@v0.5.0
    secrets: inherit
    with:
      coverage-package: mvp
      python-versions: '["3.12", "3.13"]'
      django-versions: '["5.2", "6.0"]'
```

### Docs Deployment

Reusable workflow: .github/workflows/docs.yml

Optional inputs:

- python-version (default: 3.13)
- uv-sync-args (default: empty)

Example caller workflow:

```yaml
name: Docs

on:
  push:
    branches: [main]

jobs:
  docs:
    uses: django-mvp/shared/.github/workflows/docs.yml@v0.5.0
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
    uses: django-mvp/shared/.github/workflows/release.yml@v0.5.0
    secrets: inherit
```

## Composite Actions

### publish-pypi

Composite action: .github/actions/publish-pypi

Builds the package with `uv build` and publishes it to PyPI through trusted publishing. It
has to be called from the repository's own top-level workflow, not from a reusable one, so
that the workflow reference in the OIDC token matches the trusted publisher configured on
PyPI.

Required inputs:

- ref: the git ref to check out and build

Optional inputs:

- python-version (default: 3.13)
- skip-existing (default: false): skip the upload when this version is already on PyPI

## Version Pinning Recommendation

When referencing reusable workflows from downstream projects, pin to a tag instead of main:

- Recommended: @v0.5.0
- Avoid for production stability: @main
