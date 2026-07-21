# ADR 0003 — Dependabot auto-merge stays, gated by validation

**Status:** Accepted (2026-07-21)

## Context

Weekly grouped Dependabot PRs bump the dependency bundles. Before onboarding, these
auto-merged to an unprotected `main` with no checks — on the highest-trust repo in the
family, whose workflows run downstream with `secrets: inherit`.

## Decision

Auto-merge **stays**, but `main` is protected by a ruleset whose required checks are the
validation gate (`Validate Package`, `Lint Workflows`). Auto-merge completes only when
validation is green.

## Rationale

- Hand-approving routine version bumps weekly is toil with no judgment content; automation
  is the right default.
- The risk was never auto-merge itself but *unvalidated* merge. A consistent lock file and
  a building package are exactly what a bundle bump must preserve, and the gate checks
  both.
- Breaking changes inside bumped tools (e.g. a new mypy major) surface downstream at the
  next *deliberate* tag bump, not silently — tag pinning (ADR 0001) contains the blast.

## Consequences

- A red validation check parks the Dependabot PR for human attention; that is the alert.
- Any future check added to the ruleset automatically also gates auto-merge.
