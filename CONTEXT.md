# CONTEXT.md — Domain Glossary

The ubiquitous language for this repository. Specs, issues, and reviews use these terms;
listed synonyms are avoided.

The standard defined here is adopted by the django-mvp packages and by any of Sam's other
projects that opt in. That set is not the same as the GitHub organization's membership, so
"org repos" is not a synonym for it.

- **Downstream repo** — a repository that has adopted this standard and consumes this one:
  calls its reusable workflows, installs its dependency bundles, or copies its templates.
- **Reusable workflow** — a `workflow_call` workflow under `.github/workflows/` (build,
  tests, docs, release) that downstream repos invoke from their own caller workflows.
- **Caller workflow** — the ~10-line workflow file in a downstream repo that does nothing
  but invoke a reusable workflow with repo-specific inputs. Its job names produce the
  prefixed status-check contexts (e.g. `call-build / Code Quality`).
- **Composite action** — a reusable step sequence under `.github/actions/` (publish-pypi,
  update-changelog, auto-merge-dependabot).
- **Meta-package** — the installable `mvp-shared` package. It ships no runtime code (one
  empty module); its purpose is carrying the dependency bundles. *(Avoid: "library".)*
- **Dependency bundle** — an optional-dependency extra of the meta-package (`dev`, `test`)
  that pins one version of each tool, in one place, for every downstream repo.
- **Pin tag** — the `vX.Y.Z` git tag downstream repos reference for both workflow calls
  (`@v0.1.0`) and the meta-package (git dependency `tag = "v0.1.0"`). One tag versions the
  whole standard.
- **Template** — a file under `templates/` that downstream repos copy and adapt (currently
  the shared pre-commit configuration). Copied, not linked: each repo owns its copy.
- **Validation gate** — the `Validate` workflow on this repo's own PRs (lock consistency,
  package build, workflow lint). The required checks that protect `main`.
- **Propagation** — how a standard change reaches every downstream repo: release a new pin
  tag here, then open one reviewed PR per downstream repo to bump it. Never bundled into
  feature work.
