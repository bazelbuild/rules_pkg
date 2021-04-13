# Examples of how to name packages using build time configuration.

## Examples

The examples below only show snippets of the relevant technique.
See the BUILD file for the complete source.

### Using command line flags to modify a package name

We can use a `config_setting` to capture the command line flag and then
`select()` on that to drop a part into into the name.

```
config_setting(
    name = "special_build",
    values = {"define": "SPECIAL=1"},
)

my_package_naming(
    name = "my_naming_vars",
    special_build = select({
        ":special_build": "-IsSpecial",
        "//conditions:default": "",
    }),
)
```

```
bazel build :example1
ls -l bazel-bin/example1.tar bazel-bin/RulesPkgExamples-k8-fastbuild.tar
```

```
bazel build :example1 --define=SPECIAL=1
ls -l bazel-bin/example1*.tar
```

### Using values from a toolchain in a package name.

The rule providing the naming can depend on toolchains just like a `*_library`
or `*_binary` rule

```
def _names_from_toolchains_impl(ctx):
    values = {}
    cc_toolchain = find_cc_toolchain(ctx)
    values['cc_cpu'] = cc_toolchain.cpu
    return PackageVariablesInfo(values = values)

names_from_toolchains = rule(
    implementation = _names_from_toolchains_impl,
    attrs = {
        "_cc_toolchain": attr.label(
            default = Label(
                "@rules_cc//cc:current_cc_toolchain",
            ),
        ),
    },
    toolchains = ["@rules_cc//cc:toolchain_type"],
)
```

```
bazel build :example2
ls -l bazel-bin/example2*.tar
```
