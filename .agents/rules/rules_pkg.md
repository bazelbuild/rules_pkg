---
trigger: model_decision
description: rules_pkg architecture, API design, and distribution invariants
---

# rules_pkg Invariants

## General Solutions over Format-Specific Ones
* Add features to `pkg_files` and related mapping rules so every format gets
  them. We do not accept format-specific features that the mapping rules
  could provide.
* Align attribute names across rules. Put backward-compatible aliases for old
  names in the macro wrapper, not the rule.

## Public API
* Everything under `pkg/private/` is internal. Public symbols are re-exported
  from `pkg/*.bzl`; root `*.bzl` files are compatibility shims for those.
* Every public rule attribute and macro argument needs a `doc =` string or
  docstring entry. If you touch an attribute, update its doc.
* `pkg/providers.bzl` and `providers/providers.bzl` must stay identical.
  `providers/` is published separately as `@rules_pkg_providers`; change both
  files together.

## package_variables (`$(VAR)` substitution)
1. Load `PackageVariablesInfo` from `//pkg:providers.bzl` and
   `substitute_package_variables` from `//pkg/private:util.bzl`.
2. Add the attribute:
   ```python
   "package_variables": attr.label(
       doc = """See [Common Attributes](#package_variables)""",
       providers = [PackageVariablesInfo],
   ),
   ```
3. Substitute once at the top of the implementation
   (`prefix = substitute_package_variables(ctx, ctx.attr.prefix)`) and use
   the local variable everywhere after.
4. Test with `my_package_naming` from `//tests:my_package_name.bzl`.

## Actions
* Do not write quoted strings or file path lists directly onto command lines.
  Write them to an intermediate file (see `pkg/private/manifest.py`) and pass
  that file to the tool. See
  [#214](https://github.com/bazelbuild/rules_pkg/issues/214).

## Distribution Packaging
* Only `pkg/`, `providers/`, `toolchains/`, and listed root files ship.
* Each shipped package defines a `standard_package` filegroup. When adding a
  new shipped package, add its `standard_package` to `//distro:BUILD` and to
  `//pkg:rules_pkg_lib`.
* Lines after `### INTERNAL ONLY` in `MODULE.bazel` are stripped from the
  release; put dev-only deps and repos there.
* After changing what ships, run `bazel build //distro:distro` and
  `bazel test //distro/...`.

## Vendoring
* Users vendor this tree under other paths. Do not assume packages live at
  the workspace root; resolve paths through runfiles or labels. See
  `tests/package_naming_aggregate_test.sh` for a re-rootable `sh_test`.

## Bazel Versions
* CI runs Bazel 7.x through head. Do not use features newer than the oldest
  tested release without a guard.
* Tag tests that need Bazel 8 features with `REQUIRES_BAZEL_8`; CI filters
  them out on Bazel 7.
* Changes that strictly require the latest release of Bazel may be rejected.
* Changes that behave differently under different Bazel versions may be rejected.
