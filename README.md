# MVP Shared

Shared tooling and reusable GitHub Actions workflows for downstream django-mvp repositories.

This repository provides:

- A single shared package for dev and test dependency bundles.
- Reusable CI workflows for build, test matrix, docs deploy, and release.
- Composite actions used by those workflows.
- A family-standard pre-commit template downstream repositories copy.

## Scope & philosophy

This repository is the single source of the development standard for the django-mvp
family: how every downstream repository is built, tested, linted, and released, and which
tool versions it does that with. One tagged release here versions the whole standard.

It deliberately ships no runtime code — the installable package is an empty shell whose
only job is carrying dependency bundles. It is not a Django app, not a general-purpose
actions library, and not a place for repo-specific configuration: anything only one
downstream repository needs belongs in that repository.

When choices collide: reproducibility beats convenience (pin tags, never `main`), one
family-wide standard beats per-repo flexibility, and automation is only as trusted as the
validation gating it.

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

## Pre-commit Template

`templates/pre-commit-config.yaml` is the family-standard hook set: ruff (lint + format),
mypy, and deptry running as local hooks inside the Poetry environment, with versions
supplied by the `dev` bundle. Copy it to the repository root as
`.pre-commit-config.yaml`, replace the package-directory placeholder, and enable ruff's
`UP` rules in `[tool.ruff.lint]` (they replace pyupgrade; `ruff format` replaces black).
The template's comments explain the serialised mypy hook and what runs where in CI.

## Reusable Workflows

Downstream repositories can call these workflows directly from their own workflow files.

### Build

Reusable workflow: .github/workflows/build.yml

Required inputs:

- source-dir

Optional inputs:

- python-version (default: 3.13)

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
- poetry-install-args (default: --with test)
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

## Version Pinning Recommendation

When referencing reusable workflows from downstream projects, pin to a tag instead of main:

- Recommended: @v0.1.0
- Avoid for production stability: @main
