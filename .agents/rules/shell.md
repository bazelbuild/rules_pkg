---
trigger: glob
description: Shell / Bash scripting style and portability rules
globs: "*.sh"
---

# Shell Scripting Rules

* Start scripts with `set -o errexit -o nounset -o pipefail`.
* Quote all variable expansions. Use arrays for command lines.
* Use `elif` instead of nesting `if` inside an `else` block.
* Read file lists line by line with
  `while IFS= read -r file; do ...; done < "$manifest"`, not
  `$(cat "$manifest")`.
* Prefer long option names. When a short flag is required for BSD/macOS vs.
  GNU portability, comment what it does.
* Under `set -e`, test failing commands directly (`if ! cmd; then`) instead of
  checking `$?`.
* Do not append `|| true` unless failure is expected and commented.
* Shell tests run on macOS and Windows (MSYS) too. Avoid GNU-only tools and
  flags, or guard with `target_compatible_with`.
* Locate files through runfiles rather than paths relative to the workspace
  root, so tests survive vendoring.
