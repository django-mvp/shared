# AGENTS.md — Agent Configuration for mvp-shared

<!-- Thin index only — details live in the pointed-to files. -->

This repository is the django-mvp family standard: reusable CI workflows and composite
actions that downstream repos call, the `mvp-shared` meta-package whose extras pin the
family toolchain, and templates (pre-commit) that downstream repos copy. It ships no
runtime code. See `CONTEXT.md` for the vocabulary.

## Stack & commands

- **Stack:** Poetry-managed meta-package (Python >=3.12) + GitHub Actions workflows. No
  runtime source, no test suite — validation replaces testing here.
- **Install:** `poetry install`
- **Validate lock:** `poetry check --lock`
- **Build:** `poetry build`
- **Lint workflows:** `actionlint` (over `.github/workflows/`)
- **Re-lock after bundle edits:** `poetry lock`

## Agent skills

### Issue tracker

Issues tracked in GitHub Issues via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Canonical vocabulary (needs-triage, needs-info, ready-for-agent, ready-for-human,
wontfix). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — `CONTEXT.md` at root, `docs/adr/` for standing decisions. See
`docs/agents/domain.md`. Reusable agent skills for downstream Django work live in
`.github/skills/`.

### CI checks

Required status checks (exact names): `["Validate Package", "Lint Workflows"]`.
Both come from `.github/workflows/validate.yml` on pull requests. The reusable workflows
in this repo are *called by downstream repos* and produce no checks here.

## Engineering org

This repo is operated by an autonomous engineering pipeline: feature work runs
spec→plan→tasks→implement→review→PR through org-side tooling; `specs/NNN-slug/`
directories are generated per feature. Constitution: `CONSTITUTION.md`.

**Change discipline specific to this repo:** every change lands via PR behind the
validation gate, becomes active downstream only when a new pin tag is released, and
reaches the family through per-repo propagation PRs — never silently via `@main`.
