# Guidance for AI Agents

rules_pkg is a Bazel based project. Build and run tests as done in a Bazel project.

Act as an expert in Bazel, Starlark, Python, and the package formats this
project produces (tar, zip, deb, rpm).

DO NOT `git commit` or `git push` unless given explicit permission.

## RULES TO ALWAYS FOLLOW AND NEVER IGNORE

ALWAYS FOLLOW THESE RULES. NEVER VIOLATE THEM.

Ask for user input and provide a justification if trying to violate them.

* NEVER run `bazel clean --expunge`.
* NEVER use `git commit --amend` or rebase a branch with an open PR. Create
  new commits instead.
* All features and bug fixes must have tests.
* No new third-party dependencies: no new language toolchains, no Python
  packages outside the standard library, and no new Bazel modules unless
  the Bazel team maintains them.
* Do not update dependency versions in `MODULE.bazel` or `WORKSPACE` just to
  stay at head; we support older Bazel LTS releases.

Topic-specific rules live in `.agents/rules/`. Read the ones matching the
files you touch (each rule's front matter lists its `globs` or trigger).

## Understanding the code base

rules_pkg provides Bazel rules for building distribution packages. The core
abstraction is a set of package-format-agnostic mapping rules (`pkg_files`,
`pkg_filegroup`, `pkg_mkdirs`, `pkg_mklink`) that describe *what* goes where
in a package. Format-specific rules (`pkg_tar`, `pkg_zip`, `pkg_deb`,
`pkg_rpm`) consume those descriptions.

```
pkg/            Runtime rules and providers (shipped in the distribution)
  mappings.bzl  pkg_files, pkg_filegroup, pkg_mkdirs, pkg_mklink
  providers.bzl Copy of //providers:providers.bzl (keep identical)
  private/      Internal implementation helpers (not public API)
    util.bzl    substitute_package_variables, setup_output_files, ...
    deb/ tar/ zip/  Format-specific implementations
  legacy/       Legacy pkg_rpm (spec-file based)
  releasing/    Release tooling shipped to users
providers/      The separately published @rules_pkg_providers module
toolchains/     rpmbuild and git toolchain discovery
tests/          All tests (not shipped)
examples/       Runnable examples; each is its own Bazel module, tested in CI
doc_build/      Stardoc targets that produce the reference docs
docs/           Generated reference docs served as GitHub pages
distro/         Rules to build the distribution tarball
```

Top-level `.bzl` files (`mappings.bzl`, `pkg.bzl`, etc.) are
backward-compatibility re-exports of files inside `pkg/`.

Only `pkg/`, `providers/`, `toolchains/`, and a few root files ship in the
release. Everything else is development-only.

`bazel query --output=build` can be used to inspect target definitions.
`bazel mod graph` and `bazel mod explain` show module dependencies.

## Style and conventions

Read `developers.md` and `patching.md` for the project's contribution rules.
The `.agents/rules/` files expand on them.

* Run `buildifier --lint=fix <FILE>` after editing any `.bzl` or `BUILD`
  file. Let it reorder loads and sort arguments.
* No trailing whitespace. Keep code lines under 100 columns.
* Prefer solutions that work for all package formats (via `pkg_files` /
  `pkg_filegroup`) over format-specific additions.
* All code must work on Linux, macOS, and Windows.
* Factor non-trivial scripts (multi-line shell or Python logic) into
  standalone `.sh` or `.py` files instead of inlining them via heredocs,
  `bash -c`, `python3 -c`, or multi-line workflow `run:` blocks.

## Building and testing

```
bazel test //tests/...            # everything
bazel test //tests/mappings/...   # pkg_files / pkg_filegroup
bazel test //tests/tar/...        # also deb, zip, rpm (rpm needs rpmbuild)
```

See `.agents/rules/testing.md` for test frameworks, tags, and fixtures.

## Regenerating docs

After any user-visible feature change, regenerate the reference docs:

```
bazel build //doc_build:reference
cp bazel-bin/doc_build/reference.md docs/latest.md
```

Do **not** `git commit` the result; the user handles commits.

## PRs and GitHub interaction

See `.agents/rules/pr.md`. In short:

* PRs that change behavior must be tied to an issue.
* In general, breaking behavior changes are prohibited. The new behavior must require the
  user to explicitly invoke it.
* Keep the PR description clean; it becomes the merge commit message. No AI
  disclosures, test logs, or per-file change lists in it.
* Run `bazel test //tests/...` and `buildifier` locally before opening or
  updating a PR.
* End every PR comment you post with an italicized line saying it was
  agent-generated and whether the user reviewed it.
