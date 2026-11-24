---
trigger: glob
description: Starlark language, macro, and BUILD file conventions
globs: "*.bzl,BUILD,BUILD.bazel,*.bazel"
---

# Starlark Rules

## Formatting
* Run `buildifier --lint=fix <FILE>` after every edit. Let it reorder loads
  and sort arguments.
* Use triple-quoted strings for multi-line docstrings and rule `doc` args. Do
  not use a trailing backslash after the opening triple-quote.
* Do not line-break long string literals (URLs, hashes) to fit line length.
* Use `if`/`else` statements when a ternary would exceed the line limit
  (`buildifier` collapses multi-line ternaries).

## Language Restrictions
* Starlark has no recursion. Use iterative algorithms.
* Starlark has no `while` loops. Use `for` over a bounded iterable.
* Do not write nested list comprehensions; use explicit loops.

## Macros
* In macros, canonicalize internal label references with
  `str(Label("//pkg/...:target"))` so they resolve in this module, not the
  caller's repository.
* Tag internal helper targets created by macros with `tags = ["manual"]` so
  `//...` does not build them implicitly.
* Normalize list arguments at function entry (`srcs = srcs or []`).
* Declare required parameters explicitly; forward the rest via `**kwargs`
  instead of duplicating the underlying rule's signature.
* Document `Args:` and `Returns:` for macros and helper functions.

## Rules and Providers
* Use direct attribute access (`x.field`) for fields defined on a provider
  schema instead of `getattr(x, "field", default)`.
* Prefer analysis-time validation over loading-time checks so defined but
  unbuilt targets do not fail loading.
* Prefer `ctx.actions.write` over spawning a subprocess for small content
  known at analysis time.
* Depset elements must be immutable. Use tuples or depsets, not lists, in
  providers placed into depsets.
* When returning a `struct(...)`, comment each field.

## BUILD Hygiene
* Do not use deprecated `$(location)` / `$(locations)`. Use `$(execpath)` /
  `$(execpaths)` or `$(rootpath)` as appropriate.
* Move complex loops and branching out of `BUILD` files into `.bzl` macros.
* Comment non-obvious workarounds: the intent, why the direct approach fails,
  and why the workaround works.
* Files under `tests/` that load from `/private/` paths should add a trailing
  `# buildifier: disable=bzl-visibility` comment.
