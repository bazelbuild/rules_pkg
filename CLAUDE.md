# rules_pkg — Claude Code guide

rules_pkg is a set of Bazel rules for building distribution packages (tar, zip, deb, rpm, …).
The core abstraction is a set of package-format-agnostic mapping rules (`pkg_files`,
`pkg_filegroup`, `pkg_mkdirs`, `pkg_mklink`) that describe *what* goes where in a package;
format-specific rules (`pkg_tar`, `pkg_zip`, `pkg_deb`, `pkg_rpm`) consume those descriptions.

## Repository layout

```
pkg/            Runtime rules and providers (shipped in the distribution)
  mappings.bzl  pkg_files, pkg_filegroup, pkg_mkdirs, pkg_mklink
  providers.bzl PackageVariablesInfo and other providers
  private/      Internal implementation helpers (not public API)
    util.bzl    substitute_package_variables, setup_output_files, …
    deb/        pkg_deb implementation
    tar/        pkg_tar implementation
    zip/        pkg_zip implementation
tests/          All tests (not shipped)
  mappings/     Analysis tests for pkg_files / pkg_filegroup
  tar/          Tests for pkg_tar
  deb/          Tests for pkg_deb
  rpm/          Tests for pkg_rpm
  zip/          Tests for pkg_zip
examples/       Runnable examples (tested in CI)
docs/           Generated reference docs (do not edit by hand)
distro/         Rules to build the distribution tarball
```

Top-level `.bzl` shims (`mappings.bzl`, `pkg.bzl`, etc.) are backward-compatibility
re-exports of the files inside `pkg/`.

## Code style

### Starlark / BUILD files — always run buildifier after editing

After editing any `.bzl` or `BUILD` file, run:

```
buildifier --lint=fix <FILE>
```

buildifier enforces load ordering, argument sorting, and other canonical style.
It will reorder loads alphabetically; let it.

### Starlark conventions

- All public rule attributes must have a `doc =` string.
- Use `substitute_package_variables(ctx, value)` (from `//pkg/private:util.bzl`)
  to expand `$(VAR)` make-variable syntax in string attributes.
  The rule must also declare a `package_variables` attribute typed
  `attr.label(providers = [PackageVariablesInfo])`.
- Prefer solutions that work for all package formats (via `pkg_files`/`pkg_filegroup`)
  over format-specific additions.
- Actions must not write quoted strings directly to command lines — write paths to
  an intermediate file instead.

### Python

- Python 3 only; no Python 2 support.
- Always import with full paths from the workspace root.
- No new third-party package dependencies — standard library only.

### General

- No files should have trailing whitespace.
- Try to keep lines under 100 characters long.

## Testing

**All features and bug fixes must have tests.**

### Mappings (pkg_files / pkg_filegroup)

Tests live in `tests/mappings/mappings_test.bzl` and are registered via the
`mappings_analysis_tests()` macro called from `tests/mappings/BUILD`.

- Use `pkg_files_contents_test` (defined in `mappings_test.bzl`) to assert
  expected destination paths from a `pkg_files` target.
- Use `pkg_filegroup_contents_test` to compare a `pkg_filegroup` output against
  reference `pkg_files` / `pkg_mkdirs` / `pkg_mklink` targets.
- Use `generic_negative_test` for targets that are expected to fail analysis.
- Add new test names to the `pkg_files_analysis_tests` test suite list at the
  bottom of `mappings_analysis_tests()`.

Run them with:

```
bazel test //tests/mappings/...
```

### package_variables / make-variable substitution

The sample naming rule used across tests is `my_package_naming` in
`tests/my_package_name.bzl`. Load it as:

```python
load("//tests:my_package_name.bzl", "my_package_naming")
```

Create an instance, then wire it to the `package_variables` attribute of
the rule under test. Example:

```python
my_package_naming(name = "my_vars", label = "linux_x86_64", tags = ["manual"])

pkg_files(
    name = "my_files",
    srcs = [...],
    prefix = "usr/lib/$(label)",
    package_variables = ":my_vars",
    tags = ["manual"],
)
```

### Format-specific tests

```
bazel test //tests/tar/...
bazel test //tests/deb/...
bazel test //tests/zip/...
bazel test //tests/rpm/...   # may require rpm toolchain
```

### Running everything

```
bazel test //tests/...
```

## Regenerating docs

After any feature change, regenerate the reference docs before committing:

```
bazel build //doc_build:reference
cp bazel-bin/doc_build/reference.md docs/latest.md
```

Do **not** `git commit` yet — that is a separate step the user will handle.

## Common patterns

### Adding package_variables support to an attribute

1. Import `PackageVariablesInfo` from `//pkg:providers.bzl` and
   `substitute_package_variables` from `//pkg/private:util.bzl`.
2. Add to the rule attrs:
   ```python
   "package_variables": attr.label(
       doc = """See [Common Attributes](#package_variables)""",
       providers = [PackageVariablesInfo],
   ),
   ```
3. In the implementation, call substitution at the top before using the value:
   ```python
   prefix = substitute_package_variables(ctx, ctx.attr.prefix)
   ```
4. Use the substituted local variable everywhere instead of `ctx.attr.prefix`.
5. Run `buildifier --lint=fix` on the modified file.
6. Add analysis tests in the appropriate test file.
