# Examples of how to name packages using build time configuration.

## Examples

The examples below only show snippets of the relevant technique.
See the BUILD file for the complete source.

### Using command line flags to modify a package name

We can use a `config_setting` to capture the command line flag and then
`select()` on that to drop a label into the name.

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
bazel build :my_tar
ls -l bazel-bin/my_tar.tar bazel-bin/RulesPkgExamples-k8-fastbuild.tar
```

```
bazel build :my_tar --define=SPECIAL=1
ls -l bazel-bin/my_tar.tar bazel-bin/RulesPkgExamples-k8-fastbuild-IsSpecial.tar
```

