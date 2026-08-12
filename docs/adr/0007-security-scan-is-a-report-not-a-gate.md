# ADR 0007 — The Security Scan job is a report, not a gate

**Status:** Accepted (2026-08-12)

## Context

The `security` job in `build.yml` ran bandit and safety, both piped through `|| true`, so
the job was green regardless of outcome. It reached this state with two faults, one masking
the other: `safety check --json --output safety-report.json` passes `--output` a filename
where it expects a format name, so the step errored out before writing anything, and the
blanket `|| true` on both steps hid that a broken scanner had been producing no report at
all (django-mvp/shared#23). The job was neither a gate (nothing could fail it) nor a
working report (half of it produced no output).

## Decision

**Report, not gate**, at v0.x: a finding never fails the build, but the *absence* of a
report does. Both scanner steps keep an `|| true` that swallows only the scanner's own
"issues found" exit code; a following "Verify report was produced" step asserts the
artefact exists, is non-empty, and parses as JSON, and that step carries no `|| true`. A
scanner that crashes or emits nothing now fails the job; a scanner that runs cleanly and
finds nothing to report also produces valid (empty) JSON and passes.

`safety` is replaced with `pip-audit`: safety 3.x requires an authenticated account against
its vulnerability database, which does not fit an unattended CI job; pip-audit needs none.

## Rationale

- Arming findings as a hard gate now would turn every family repo red on the next scan with
  no chance to triage first — the risk noted when this was filed. A report first, gate
  later once the family has looked at what it actually surfaces.
- The failure mode this fixes was specifically a broken scanner *looking* clean. Gating on
  the artefact rather than the tool's exit code is what catches that class of bug — a
  scanner that finds nothing legitimately still writes a valid, empty report; one that
  crashes writes nothing at all, and only the second is a build failure.

## Consequences

- Findings are visible only via the uploaded `bandit-report` / `pip-audit-report`
  artefacts; nobody is notified, and no PR is blocked, until a follow-up decides to arm one
  or both as a gate.
- Revisit this ADR once the family has seen a few cycles of real report output and can set
  an informed bar for what should fail a build.
