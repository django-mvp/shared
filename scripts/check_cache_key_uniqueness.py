#!/usr/bin/env python3
"""Fail if two jobs that run concurrently in the same workflow would share a
dependency cache key.

Every environment setup step resolves to a cache key built from the runner OS,
the requested Python version, the package manager version, the install/sync
arguments, a caller-supplied suffix, and the lockfile hash. Call sites requesting
the same series resolve to the same patch release within a run, so modelling the
requested version here answers the uniqueness question exactly; whether the key
pins the *resolved* interpreter is a separate property, checked by
check_venv_cache_safety.py.

Two call sites in the same workflow file that resolve to an identical tuple race
to save the same cache entry when they run without a `needs` relationship between
them (see django-mvp/shared#22): each starts from a cache miss, each installs its
own dependencies, and both then try to save under the same key. Only one save
wins; the loser's attempt is wasted, and the class of bug this produces (an
incomplete or unexpected environment being restored by a job that never itself
wrote it) is exactly the intermittent "packages not installed despite a cache
hit" failure reported in #22.

This script computes the resolved key tuple for every setup call site (expanding
the tests.yml matrix) and fails if any two are identical. Collisions are looked
for within each action rather than across them, because the two actions cache
different things under different key schemes: setup-poetry caches `.venv`,
setup-uv caches uv's global package cache.
"""

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
ACTIONS_DIR = REPO_ROOT / ".github" / "actions"
ACTION_REF_PREFIX = "django-mvp/shared/.github/actions/"

# docs.yml is excluded because it has a single call site per action and so cannot
# collide with itself.
CHECKED_WORKFLOWS = ("build.yml", "tests.yml")


class SetupAction:
    """One environment-setup composite action, and the cache keys that its call
    sites across the reusable workflows resolve to."""

    def __init__(self, name, version_input, args_input):
        self.name = name
        self.version_input = version_input
        self.args_input = args_input

    @property
    def ref(self):
        return f"{ACTION_REF_PREFIX}{self.name}"

    def default_version(self):
        action_doc = yaml.safe_load(
            (ACTIONS_DIR / self.name / "action.yml").read_text()
        )
        return action_doc["inputs"][self.version_input]["default"]

    def call_sites(self, doc):
        """Yield (job_id, with-block) for every step in `doc` using this action."""
        for job_id, job in doc["jobs"].items():
            for step in job.get("steps") or []:
                if step.get("uses", "").startswith(self.ref):
                    yield job_id, step.get("with", {}) or {}

    def keys_for_build(self, doc, version):
        keys = []
        for job_id, with_block in self.call_sites(doc):
            key = (
                with_block.get("python-version", "3.13"),
                version,
                with_block.get(self.args_input, ""),
                with_block.get("cache-key-suffix", ""),
            )
            keys.append(("build.yml", job_id, key))
        return keys

    def keys_for_tests(self, doc, version):
        # PyYAML parses the bare `on:` key as the boolean True (YAML 1.1), not the
        # string "on" — a well-known GitHub Actions YAML parsing gotcha.
        on_block = doc.get("on", doc.get(True))
        inputs = on_block["workflow_call"]["inputs"]
        python_versions = yaml.safe_load(inputs["python-versions"]["default"])
        django_versions = yaml.safe_load(inputs["django-versions"]["default"])
        default_args = inputs[self.args_input]["default"]

        keys = []
        for _job_id, with_block in self.call_sites(doc):
            args_expr = with_block.get(self.args_input, "")
            suffix_expr = with_block.get("cache-key-suffix", "")
            for python_version in python_versions:
                for django_version in django_versions:
                    # Resolve the two GitHub Actions expressions this script cares
                    # about by substituting the matrix values a real run would use.
                    args = (
                        default_args
                        if f"inputs.{self.args_input}" in args_expr
                        else args_expr
                    )
                    suffix = (
                        django_version
                        if "matrix.django-version" in suffix_expr
                        else suffix_expr
                    )
                    leg = f"python={python_version},django={django_version}"
                    keys.append(
                        ("tests.yml", leg, (python_version, version, args, suffix))
                    )
        return keys

    def collisions(self, docs):
        version = self.default_version()
        keys = self.keys_for_build(docs["build.yml"], version) + self.keys_for_tests(
            docs["tests.yml"], version
        )

        by_key = {}
        for workflow, call_site, key in keys:
            by_key.setdefault(key, []).append(f"{workflow}:{call_site}")

        return len(keys), {k: sites for k, sites in by_key.items() if len(sites) > 1}


ACTIONS = (
    SetupAction("setup-poetry", "poetry-version", "poetry-install-args"),
    SetupAction("setup-uv", "uv-version", "uv-sync-args"),
)


def main():
    docs = {
        name: yaml.safe_load((WORKFLOWS_DIR / name).read_text())
        for name in CHECKED_WORKFLOWS
    }

    failed = False
    for action in ACTIONS:
        count, collisions = action.collisions(docs)
        if collisions:
            failed = True
            print(
                f"Cache key collisions found for {action.name} (django-mvp/shared#22):",
                file=sys.stderr,
            )
            for key, sites in collisions.items():
                print(f"  key={key}", file=sys.stderr)
                for site in sites:
                    print(f"    - {site}", file=sys.stderr)
        else:
            print(f"No cache key collisions across {count} {action.name} call sites.")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
