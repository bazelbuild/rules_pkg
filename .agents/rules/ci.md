---
trigger: glob
description: BazelCI and GitHub Actions configuration conventions
globs: ".bazelci/**,.github/**,.bcr/**"
---

# CI Configuration Rules

## BazelCI (`.bazelci/`)
* `presubmit.yml` only imports the other files. Put test matrices in
  `tests.yml`, `integration.yml`, and `examples_*.yml`.
* Reuse the YAML anchors (`*default_tests`, `*win_tests`, ...) instead of
  copying target lists.
* Exclude rpm tests on platforms without `rpmbuild` via the existing
  `default_tests` anchor; use `default_tests_with_rpm` where it is available.
* Each new example under `examples/` needs its own `examples_*.yml` entry
  with `working_directory` set to that example.

## GitHub Actions (`.github/workflows/`)
* Declare explicit top-level `permissions:` (`contents: read` or `{}`).
* Never interpolate `${{ ... }}` directly into `run:` blocks. Bind values to
  `env:` and reference them as quoted shell variables.
* Treat branch names, PR titles, and comment bodies as untrusted input.
* Keep step logic in scripts (e.g. `checks.sh`, `release_prep.sh`), not
  multi-line `run:` blocks.
* Never pass `--stamp` on pull request builds.

## Releases (`.bcr/`, `release*.yml`)
* Do not change release or BCR publishing config unless asked.
