# ADR 0002 — One repo carries the whole family standard

**Status:** Accepted (2026-07-21)

## Context

The family standard has three parts: reusable CI workflows, the shared toolchain (the
`dev`/`test` dependency bundles), and copyable templates (pre-commit). These could live in
separate repos (e.g. a dedicated dev-tools package) or together.

Historically the toolchain lived in `fairdm-dev-tools`, making generic django-mvp packages
depend on a domain-specific repo — the dependency direction was backwards: the domain
framework (fairdm) should consume the generic family standard, not define it.

## Decision

**This repo (`django-mvp/shared`) carries all of it**: workflows, composite actions, the
`mvp-shared` meta-package with its bundles, templates, and shared agent skills. It
replaces `fairdm-dev-tools` as the toolchain source for all family repos.

## Rationale

- One home means one version stream: a single pin tag answers "which standard," covering
  CI behaviour and tool versions together — they usually change together.
- One propagation source: a standard change is one release here plus one bump PR per
  downstream repo, regardless of which part changed.
- Correct dependency direction: generic family standard at the bottom; domain frameworks
  (fairdm) consume it like any other downstream repo.

## Consequences

- Downstream repos swap `fairdm-dev-tools` for `mvp-shared` (one git-dependency line).
- `fairdm-dev-tools` becomes a consumer-side concern of the fairdm family and can be
  retired or reduced to fairdm-specific extras.
- A toolchain-only change still cuts a repo-wide tag; acceptable, since tags are cheap and
  callers upgrade deliberately.
