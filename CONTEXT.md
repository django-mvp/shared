# CONTEXT.md — Domain Glossary

The ubiquitous language for this repository. Specs, issues, and reviews use these terms;
listed synonyms are avoided.

- **Family** — the set of repositories that share this standard: the django-mvp packages
  and any of Sam's projects that adopt it. *(Avoid: "org repos" — GitHub organization
  membership and family membership are not the same thing.)*
- **Downstream repo** — a family repository that consumes this one: calls its reusable
  workflows, installs its dependency bundles, or copies its templates.
- **Reusable workflow** — a `workflow_call` workflow under `.github/workflows/` (build,
  tests, docs, release) that downstream repos invoke from their own caller workflows.
- **Caller workflow** — the ~10-line workflow file in a downstream repo that does nothing
  but invoke a reusable workflow with repo-specific inputs. Its job names produce the
  prefixed status-check contexts (e.g. `call-build / Code Quality`).
- **Composite action** — a reusable step sequence under `.github/actions/` (setup-poetry,
  publish-pypi, update-changelog, auto-merge-dependabot) used by the reusable workflows.
- **Meta-package** — the installable `mvp-shared` package. It ships no runtime code (one
  empty module); its purpose is carrying the dependency bundles. *(Avoid: "library".)*
- **Dependency bundle** — an optional-dependency extra of the meta-package (`dev`, `test`)
  that pins the family's toolchain versions in one place.
- **Pin tag** — the `vX.Y.Z` git tag downstream repos reference for both workflow calls
  (`@v0.1.0`) and the meta-package (git dependency `tag = "v0.1.0"`). One tag versions the
  whole standard.
- **Template** — a file under `templates/` that downstream repos copy and adapt (currently
  the family pre-commit configuration). Copied, not linked: each repo owns its copy.
- **Validation gate** — the `Validate` workflow on this repo's own PRs (lock consistency,
  package build, workflow lint). The required checks that protect `main`.
- **Propagation** — how a standard change reaches the family: release a new pin tag here,
  then open one reviewed PR per downstream repo to bump it. Never bundled into feature work.
