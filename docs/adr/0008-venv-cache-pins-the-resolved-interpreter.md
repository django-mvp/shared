# ADR 0008 — The venv cache pins the resolved interpreter, and the dependency install is unconditional

**Status:** Accepted (2026-08-12)

## Context

`setup-poetry` caches `.venv` so a warm run skips a full `poetry install`. Two decisions in
that step turned out to be load-bearing in a way nobody had written down, and both were wrong.

The cache key interpolated `inputs.python-version`, the version a caller *asks* for. Every
caller asks for a series — `3.13` — and GitHub's hosted tool cache resolves that to whichever
patch release the runner image currently ships. A Poetry in-project venv is not relocatable
across that boundary: `.venv/pyvenv.cfg` records `home` and `base-executable` as absolute
paths into `/opt/hostedtoolcache/Python/<patch>/x64`. When the image rolled from 3.13.14 to
3.13.15, every stored entry became a venv pointing at an interpreter that no longer existed,
while still matching the key.

Poetry does not repair such a venv. It logs "The virtual environment found in .venv seems to
be broken", deletes it and builds an empty one. It does that lazily, on the next command that
needs the environment — which is `Install project`, one step *after* the cache-hit condition
on `Install dependencies` has already been evaluated and found true. So the dependency install
was skipped, the venv was then emptied, and nothing put anything back. The job ran on a venv
holding the project and none of its dependencies, and died at the first `poetry run` with
`Command not found: pytest`.

The two faults are independent and compose badly. The key made poisoned entries common; the
condition made every poisoned entry fatal rather than merely slow. Observed on FAIR-DM/fairdm
PR #125, where the Django 5.2 matrix leg landed on 3.13.14 and passed while the Django 5.1 leg
landed on 3.13.15 and failed, on the same commit, minutes apart. The Django version was
incidental — it was the runner each leg happened to get.

## Decision

**The cache key and every restore-key carry `steps.setup-python.outputs.python-version`**, the
patch release `actions/setup-python` actually resolved, rather than the series that was
requested. A venv is therefore never offered to a runner it cannot execute. The `setup-python`
step carries an `id` for the sole purpose of exposing that output.

**`Install dependencies` runs unconditionally.** A cache hit is treated as a head start, not as
proof that the environment is complete. Against a healthy restored venv the command resolves to
no operations and costs a few seconds; against one Poetry has just recreated it is the only
thing that refills it.

Both properties are enforced by `scripts/check_venv_cache_safety.py`, wired into `validate.yml`.
Neither is visible in a normal run — reproducing the failure needs a stored cache entry, a
runner image roll, and the two to arrive in the wrong order — so a static check is the only
place this can be caught before it fires on somebody else's release.

## Consequences

- A patch-release roll now costs one cold install per (series, patch) pair instead of poisoning
  every cached entry. Cache entries for the superseded patch age out on their own.
- Every run pays a short no-op `poetry install --no-root`, including warm ones. That is the
  price of the guarantee and it is small next to the install it protects.
- Making the install unconditional also closes a quieter hole. Two of the three `restore-keys`
  drop `poetry-install-args` and `cache-key-suffix`, so a job wanting `--with test` could
  already restore a venv saved by one that did not have those groups. That used to ship a venv
  missing the test dependencies; it is now topped up.
- This is the third cache defect in the same action, after the key collision in #22 and this
  pair. The generalisation worth keeping: **a cache key must name every input the cached
  artifact is not portable across**, and a restore must never be trusted as a substitute for
  the step that builds the thing.
