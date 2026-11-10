---
trigger: model_decision
description: Linux, macOS, and Windows portability requirements
---

# Portability Rules

* All code must work on Linux, macOS, and Windows. CI tests all three.
* When code exists only for portability, comment why so a later maintainer
  does not revert it.
* Features that cannot work everywhere must be optional. Platform-specific
  functionality belongs in a distinct, opt-in module.
* Favor tests that auto-skip on unsupported platforms
  (`target_compatible_with`) over CI exclusion lists.
* Paths inside archives always use `/`. Normalize host paths before writing
  them into tar, zip, deb, or rpm entries.
* Do not rely on symlinks, executable bits, or case-sensitive file names
  existing on the host; Windows checkouts may lack all three.
* Allow an optional `.exe` suffix when matching tool names in test output.
