#!/usr/bin/env python3
"""Fail if the setup-poetry venv cache can hand a job an unusable environment.

Two properties of `.github/actions/setup-poetry/action.yml` have to hold together,
and each one is a single edit away from being lost. ADR 0008 records why.

1. The cache key carries the interpreter `setup-python` actually resolved, not the
   series that was requested. A Poetry in-project venv records absolute interpreter
   paths in `.venv/pyvenv.cfg`, so one built against 3.13.14 is broken on a runner
   image carrying 3.13.15. Keying on `inputs.python-version` (`3.13`) let the hosted
   tool cache rolling a patch poison every stored entry at once.

2. The dependency install runs unconditionally. Poetry does not repair a venv it
   considers broken, it replaces it with an empty one, and it does that during
   `Install project` — after the cache-hit condition has already been evaluated.
   Gating the dependency install on a cache miss therefore leaves the empty venv
   empty, and the job fails at the first `poetry run` with a bare "Command not
   found". Property 1 makes that rare; only property 2 makes it survivable.

Checking these statically is worth a script because neither shows up in a normal
run. The failure needs a cache entry, a runner image roll, and the two to land in
the wrong order, so it is invisible until it fires on somebody's release.
"""

import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
ACTION_FILE = REPO_ROOT / ".github" / "actions" / "setup-poetry" / "action.yml"

# The expression the key must interpolate: setup-python's resolved output.
RESOLVED_VERSION_EXPR = re.compile(
    r"steps\.[A-Za-z0-9_-]+\.outputs\.python-version"
)
# The expression it must not: the requested series.
REQUESTED_VERSION_EXPR = re.compile(r"inputs\.python-version")


def _cache_step(steps):
    for step in steps:
        if step.get("uses", "").startswith("actions/cache@"):
            return step
    return None


def _install_dependencies_step(steps):
    for step in steps:
        if step.get("name") == "Install dependencies":
            return step
    return None


def _setup_python_step(steps):
    for step in steps:
        if step.get("uses", "").startswith("actions/setup-python@"):
            return step
    return None


def check_key_pins_resolved_interpreter(steps):
    """Property 1."""
    failures = []

    setup_python = _setup_python_step(steps)
    if setup_python is None:
        return ["no actions/setup-python step found"]
    if not setup_python.get("id"):
        failures.append(
            "the actions/setup-python step has no `id`, so its resolved "
            "python-version output cannot be referenced in the cache key"
        )

    cache = _cache_step(steps)
    if cache is None:
        return failures + ["no actions/cache step found"]

    with_block = cache.get("with", {})
    key = with_block.get("key", "")
    restore_keys = with_block.get("restore-keys", "") or ""
    fragments = [("key", key)] + [
        (f"restore-keys line {n}", line)
        for n, line in enumerate(restore_keys.splitlines(), start=1)
        if line.strip()
    ]

    for label, fragment in fragments:
        if not RESOLVED_VERSION_EXPR.search(fragment):
            failures.append(
                f"{label} does not interpolate the resolved interpreter "
                f"(steps.<setup-python>.outputs.python-version): {fragment.strip()}"
            )
        if REQUESTED_VERSION_EXPR.search(fragment):
            failures.append(
                f"{label} interpolates the requested series "
                f"(inputs.python-version), which does not distinguish patch "
                f"releases: {fragment.strip()}"
            )

    return failures


def check_dependency_install_is_unconditional(steps):
    """Property 2."""
    step = _install_dependencies_step(steps)
    if step is None:
        return ["no step named 'Install dependencies' found"]
    if "if" in step:
        return [
            "the 'Install dependencies' step is conditional "
            f"(if: {step['if']}). It must run unconditionally, or a venv that "
            "Poetry recreates during 'Install project' is never refilled."
        ]
    return []


def main():
    action = yaml.safe_load(ACTION_FILE.read_text())
    steps = action["runs"]["steps"]

    failures = check_key_pins_resolved_interpreter(steps)
    failures += check_dependency_install_is_unconditional(steps)

    if failures:
        print(
            "setup-poetry venv cache is unsafe (see ADR 0008):",
            file=sys.stderr,
        )
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    print("setup-poetry venv cache pins the resolved interpreter and always installs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
