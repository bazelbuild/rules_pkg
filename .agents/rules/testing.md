---
trigger: model_decision
description: How to write, tag, and run rules_pkg tests
---

# Testing Rules

## Requirements
* All behavioral changes need tests. For a bug fix, add a test that fails
  before the fix and passes after.
* Prefer many small unit tests over one test that checks many conditions.
  Favor analysis and unit tests over integration tests.
* Place tests by feature tested (`tests/tar/`, `tests/deb/`, ...), not by the
  helper they use.

## Running
* `bazel test //tests/...` runs everything. Scope to the area you changed
  first (`bazel test //tests/mappings/...`).
* `//tests/rpm/...` and `//pkg/legacy/tests/rpm/...` need `rpmbuild` on the
  host; they are excluded on platforms without it.
* Examples are separate modules. Test them from their own directory:
  `cd examples/<name> && bazel test //...`.
* Use `--test_verbose_timeout_warnings` to find tests with oversized `size`.

## Starlark Analysis Tests
* Use `@bazel_skylib//lib:unittest.bzl` (`analysistest`, `asserts`). Do not
  add `rules_testing`; it is not a dependency.
* Mapping tests live in `tests/mappings/mappings_test.bzl`, registered from
  `mappings_analysis_tests()`:
  * `pkg_files_contents_test` asserts destination paths of a `pkg_files`.
  * `pkg_filegroup_contents_test` compares a `pkg_filegroup` against
    reference `pkg_files` / `pkg_mkdirs` / `pkg_mklink` targets.
  * `generic_negative_test` asserts a target fails analysis.
  * Add new test names to the `pkg_files_analysis_tests` suite at the bottom
    of `mappings_analysis_tests()`.
* Tag fixture targets under test `manual` so `//...` does not build them.

## Archive Content Tests
* Use `verify_archive_test` from `//pkg:verify_archive.bzl` to check that a
  built archive contains (or lacks) specific paths, links, and modes.
* Use format-specific Python tests (`tests/tar/`, `tests/zip/`,
  `tests/deb/`) for byte-level or metadata checks.

## Tags and Platforms
* `nowindows`: test cannot run on Windows; CI filters it there. Prefer
  `target_compatible_with` when the reason is a platform constraint, so the
  test auto-skips without CI exclusion lists.
* `REQUIRES_BAZEL_8`: test needs Bazel 8 features; filtered on Bazel 7.
* Do not disable tests on Windows for convenience. Comment why any platform
  restriction exists.
