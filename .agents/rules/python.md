---
trigger: glob
description: Python coding and unittest conventions for rules_pkg tools
globs: "*.py,*.py.tpl"
---

# Python Conventions

## Compatibility and Dependencies
* Python 3 only. Stay compatible with Python 3.12.
* Standard library only. No new third-party packages.
* Import with full paths from the workspace root
  (`from pkg.private import manifest`), never relative imports.
* Never alter `sys.path`.
* List each package's `__init__.py` in its `py_library` `srcs`; do not create
  init-only wrapper targets.

## Code
* Use direct attribute access (`args.foo`) on `argparse.Namespace`; avoid
  defensive `getattr()`.
* Do not add silent no-op guards (`if path.exists():`) that mask broken
  invocations; let errors surface.
* Let errors bubble up from helpers instead of printing and returning failure
  sentinels.
* Inherit custom exceptions from `Exception`, not `RuntimeError`.
* Prefix private module-level constants and helpers with `_`.
* Include a `Usage:` example and input format in CLI module docstrings.
* Archive writers must produce reproducible output: fixed timestamps, sorted
  entries, normalized paths, and explicit modes and owners.

## Tests
* Write tests with `unittest` and run them via `py_test`.
* Use real temporary files (`tempfile`, `TEST_TMPDIR`) instead of mocking file
  IO.
* Locate test data through runfiles (`python.runfiles`), not hard-coded
  workspace paths, so tests work when vendored.
* Assert against literal expected values rather than reimplementing the
  production logic.
* Factor repeated assertion blocks into `_assert_*` helpers.
