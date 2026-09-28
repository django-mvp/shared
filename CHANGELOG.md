# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `templates/ruff-base.toml` selects ruff's pydocstyle rules (`D`) with the Google
  convention. `D106` and `D107` are ignored, and tests, migrations and `conftest.py` are
  exempt.
- `pydoclint` in the `dev` bundle, and a `pydoclint` hook in
  `templates/pre-commit-config.yaml` that checks docstring sections against each
  signature.

### Changed

- A package's own per-file ignores now go under
  `[tool.ruff.lint.extend-per-file-ignores]`. A `[tool.ruff.lint.per-file-ignores]` table
  replaces the base file's table, so the docstring exemptions for tests would be lost.

### Removed

- `django-coverage-plugin` from the `test` bundle. Templates are not measured for
  coverage. A package that enables the plugin in its own coverage configuration has to
  remove that setting when it moves to this release.
