#!/usr/bin/env python3
"""Fail if two jobs that run concurrently in the same workflow would share a
Poetry venv cache key.

Every "Set up Poetry env" step resolves to a cache key built from
(runner.os, resolved python-version, poetry-version, poetry-install-args,
cache-key-suffix, poetry.lock hash). Call sites requesting the same series resolve
to the same patch release within a run, so modelling the requested version here
answers the uniqueness question exactly; whether the key pins the *resolved*
interpreter is a separate property, checked by check_venv_cache_safety.py.
Two call sites in the same workflow file that resolve to an
identical tuple race to save the same cache entry when they run without a
`needs` relationship between them (see django-mvp/shared#22): each starts from
a cache miss, each runs its own `poetry install`, and both then try to save
under the same key. Only one save wins; the loser's attempt is wasted, and the
class of bug this produces (an incomplete or unexpected venv being restored by
a job that never itself wrote it) is exactly the intermittent "packages not
installed despite a cache hit" failure reported in #22.

This script computes the resolved key tuple for every setup-poetry call site
(expanding the tests.yml matrix) and fails if any two are identical.
"""

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
ACTION_FILE = REPO_ROOT / ".github" / "actions" / "setup-poetry" / "action.yml"
ACTION_REF = "django-mvp/shared/.github/actions/setup-poetry"


def default_poetry_version():
    action_doc = yaml.safe_load(ACTION_FILE.read_text())
    return action_doc["inputs"]["poetry-version"]["default"]


def _find_setup_poetry_steps(job_id, job):
    steps = job.get("steps") or []
    for step in steps:
        uses = step.get("uses", "")
        if uses.startswith(ACTION_REF):
            yield step.get("with", {}) or {}


def keys_for_build(doc, poetry_version):
    keys = []
    for job_id, job in doc["jobs"].items():
        for with_block in _find_setup_poetry_steps(job_id, job):
            python_version = with_block.get("python-version", "3.13")
            poetry_install_args = with_block.get("poetry-install-args", "")
            cache_key_suffix = with_block.get("cache-key-suffix", "")
            keys.append(
                (
                    "build.yml",
                    job_id,
                    (python_version, poetry_version, poetry_install_args, cache_key_suffix),
                )
            )
    return keys


def keys_for_tests(doc, poetry_version):
    # PyYAML parses the bare `on:` key as the boolean True (YAML 1.1), not the
    # string "on" — a well-known GitHub Actions YAML parsing gotcha.
    on_block = doc.get("on", doc.get(True))
    inputs = on_block["workflow_call"]["inputs"]
    python_versions = yaml.safe_load(inputs["python-versions"]["default"])
    django_versions = yaml.safe_load(inputs["django-versions"]["default"])
    default_install_args = inputs["poetry-install-args"]["default"]

    keys = []
    for job_id, job in doc["jobs"].items():
        for with_block in _find_setup_poetry_steps(job_id, job):
            poetry_install_args_expr = with_block.get("poetry-install-args", "")
            cache_key_suffix_expr = with_block.get("cache-key-suffix", "")
            for python_version in python_versions:
                for django_version in django_versions:
                    # Resolve the two GitHub Actions expressions this script cares
                    # about by substituting the matrix values a real run would use.
                    poetry_install_args = (
                        default_install_args
                        if "inputs.poetry-install-args" in poetry_install_args_expr
                        else poetry_install_args_expr
                    )
                    cache_key_suffix = (
                        django_version
                        if "matrix.django-version" in cache_key_suffix_expr
                        else cache_key_suffix_expr
                    )
                    leg = f"python={python_version},django={django_version}"
                    keys.append(
                        (
                            "tests.yml",
                            leg,
                            (python_version, poetry_version, poetry_install_args, cache_key_suffix),
                        )
                    )
    return keys


def main():
    build_doc = yaml.safe_load((WORKFLOWS_DIR / "build.yml").read_text())
    tests_doc = yaml.safe_load((WORKFLOWS_DIR / "tests.yml").read_text())
    poetry_version = default_poetry_version()

    all_keys = keys_for_build(build_doc, poetry_version) + keys_for_tests(tests_doc, poetry_version)

    by_key = {}
    for workflow, call_site, key in all_keys:
        by_key.setdefault(key, []).append(f"{workflow}:{call_site}")

    collisions = {key: sites for key, sites in by_key.items() if len(sites) > 1}

    if collisions:
        print("Cache key collisions found (django-mvp/shared#22):", file=sys.stderr)
        for key, sites in collisions.items():
            print(f"  key={key}", file=sys.stderr)
            for site in sites:
                print(f"    - {site}", file=sys.stderr)
        return 1

    print(f"No cache key collisions across {len(all_keys)} setup-poetry call sites.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
