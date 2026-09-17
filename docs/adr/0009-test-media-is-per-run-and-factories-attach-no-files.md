# ADR 0009 — Test media goes to a per-run directory, and factories attach no file unless asked

**Status:** Accepted (2026-09-17)

## Context

FairDM's test settings pointed `MEDIA_ROOT` and `STATIC_ROOT` at fixed paths under the system
temporary directory. Its factories declared `factory.django.ImageField`, which writes a real
JPEG on every instantiation, and the upload path put each one in a directory of its own. Every
run of the suite therefore wrote into the same place, and nothing ever removed it.

On 1 September that directory took the development machine to zero free inodes: 1,048,576 of
1,048,576 used, 93% of them one project's test images. Disk usage was 43%, so `df -h` looked
healthy while every attempt to create a temporary file failed with `ENOSPC`, in tooling that
had nothing to do with the test suite. It was cleared by hand. By 17 September it held 450,585
files and 1.8 GB again, with the filesystem back to 98% inode use.

The part that makes this a family concern rather than one repo's untidiness is that the leak
travels with the package. A factory is shipped code. Any downstream project that installs the
package and uses its factories inherits the file writing, and inherits it without inheriting
the settings that would contain it. GHFDB Portal, which builds on FairDM, had 46,338 files and
370 MB under its own `media/` directory, every one of them the same `example.jpg`, accumulated
over three weeks. The directory is gitignored, which is exactly why nobody noticed.

An audit of the fourteen repositories in the family found this is not widespread today. Ten
write no files during their tests at all. django-literature already binds `MEDIA_ROOT` to a
per-test `tmp_path` in its conftest, deliberately. FairDM was the only one with the fixed path.
The rule is written down now because the next package to add a file-writing factory should not
have to rediscover any of the above, and because the second half of it is a packaging
obligation that a downstream repository cannot fix for itself.

## Decision

**A repository whose tests can write media points `MEDIA_ROOT` — and `STATIC_ROOT` where
anything writes to it — at a directory the test runner creates for the run and removes
afterwards.** Never a fixed path: not under the system temporary directory, and not inside the
working tree. pytest's `tmp_path` and `tmp_path_factory` are the mechanism, and whatever is
chosen has to hold under `pytest-xdist`, where each worker is a separate process with its own
fixture instances.

**A factory that can attach a file attaches none unless the caller asks for one.** The default
build leaves the field empty and writes nothing. Producing a real file is opt-in, through the
field's own argument:

```python
ProjectFactory()             # no image, nothing written to disk
ProjectFactory(image=True)   # a real image file, for tests that assert one renders
```

The option stays because it is needed. A test that checks an image renders correctly cannot do
it against an empty field. What changes is which of the two is the default.

These are two independent obligations, not one rule stated twice. The first protects the
repository that holds the tests. The second is the only one that reaches a downstream consumer,
because consumers inherit the factories and not the settings.

## Consequences

- No repository in the family needs changing to comply, except FairDM, which is where the
  defect was found (FAIR-DM/fairdm#323).
- The factory change is a behaviour change for anyone downstream whose tests assumed a factory
  produced an image. The fix at each call site is one argument, `image=True`.
- Neither rule is visible from outside the repository that holds it, so there is nothing for the
  shared workflows to enforce and no check is added here. Each repository proves its own
  compliance in its own suite, and a test that asserts `MEDIA_ROOT` lies under the run's
  temporary directory is cheap enough that there is no excuse for leaving it out.
- A fixed path under the system temporary directory is the worse of the two fixed-path
  mistakes, and worth naming as such. Junk in the working tree is at least in front of the
  person who made it. A shared temporary directory charges the cost to a resource that
  unrelated software depends on, and inode exhaustion surfaces as failures nowhere near the
  thing that caused it.
- The generalisation worth keeping: **a test fixture that writes outside the run's own
  directory is a leak, whether or not anyone has noticed the bill yet.** The reason this one
  ran for three weeks in two repositories is that both wrote somewhere nobody looks.
