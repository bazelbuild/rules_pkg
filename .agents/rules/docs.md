---
trigger: glob
description: Reference doc generation and documentation conventions
globs: "docs/**,doc_build/**,*.md"
---

# Documentation Rules

* `docs/latest.md` is generated. Never edit it by hand. Regenerate with:
  ```
  bazel build //doc_build:reference
  cp bazel-bin/doc_build/reference.md docs/latest.md
  ```
* Older `docs/<version>/` files are release snapshots; do not edit them.
* Write user-facing docs in rule and attribute docstrings; stardoc renders
  them. Keep docstrings brief: purpose, arguments, and behavior.
* Hand-written sections live in `doc_build/common.md` (common attributes such
  as `package_variables`) and `doc_build/toc.md.tpl`.
* When adding a new public rule or provider, add it to `ORDER` in
  `doc_build/BUILD` so it appears in the reference.
* Document user-visible behavior, not internal workarounds.
* Wrap hand-written Markdown at 80 columns.
