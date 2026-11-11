---
trigger: glob
description: Cross-language code style and API design conventions
globs: "*.py,*.sh,*.bzl,*.bazel,BUILD,*.yaml,*.yml"
---

# Code Style Rules

## General
* No trailing whitespace. Files end with a newline.
* Keep lines under 100 columns.
* Match the comment density, naming, and idioms of surrounding code.

## Control Flow & API Design
* Trace existing call graphs before adding new rules, macros, or attributes.
  Wire new inputs into the existing pipeline at the narrowest seam.
* Do not modify existing behavior unless required; justify every changed
  line in existing files.
* Split large changes: send a behavior-preserving refactor PR first, then a
  smaller PR with the new behavior.
* Keep parameter and return types uniform across callers (always
  `list[str]`, never `str | list[str]`). Fix callers instead of adding runtime
  type branches.
* Use early-return guard clauses over deeply nested conditionals.
* When branching on modes, make the fall-through `else` the error case.
* Accept one form per input. Do not add unrequested modes, knobs, or aliases.
  Create test fixture files instead of test-only code paths.
* Omit speculative precondition checks when the underlying operation fails
  clearly on its own.
* Break long or compound inline expressions into named intermediate
  variables.
* When a value holds relative paths, document what they are relative to.

## Sorting
* Keep lists of sources, deps, and registry tables sorted. Let `buildifier`
  sort Starlark lists.
