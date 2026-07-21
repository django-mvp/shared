# Domain docs layout

Single-context layout:

- **`CONTEXT.md`** (repo root) — the glossary. Every core concept of the family standard
  (reusable workflow, caller, meta-package, bundle, pin tag, template, propagation) is
  defined there; specs and reviews use that vocabulary.
- **`docs/adr/`** — one file per standing architectural decision. Read before proposing
  structural changes; a decision is revisited by superseding its ADR, not by silently
  contradicting it.
- **`.github/skills/`** — reusable agent skills shipped *to downstream repos* (django-cotton,
  pytest-django testing). They are part of the distributed standard, not documentation of
  this repo.

The README is the adopter-facing front door (what this repo provides and how downstream
repos consume it); CONTEXT.md and the ADRs are the working-context layer.
