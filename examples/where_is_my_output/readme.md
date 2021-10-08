# Where are my files?

## Finding the exact path to the files created by a target.

Most of the time, Bazel users do not need to know the path to the artifacts
created for any given target. A notable exception is for users of packaging
rules. You typically create an RPM or Debian packaged file for the explicit
purpose of taking it from your machine and giving it to someon else.

Users often create scripts to push `bazel build` outputs to other places and
need to know the path to those outputs. This can be a challenge for rules which
may create the file name by combining a base part with a version number,
and maybe a CPU architecture. We don't do find them with shell wildcards
like `bazel-bin/my-pkg/pkg-*.deb`. That is brittle. Fortunately, Bazel
provide all the tools we need to get the pricise path to an output.

## Using cquery to find the exact path to the outputs created for a target.

We can use Bazel's cquery command to find information about a target.
Specifically we use
[cquery's Starlark output](https://docs.bazel.build/versions/main/cquery.html#cquery-starlark-dialect)
to inspect a target and print exactly what we need. Let's try it:

```shell
bazel build :deb
bazel cquery :deb --output=starlark --starlark:file=show_deb_outputs.bzl 2>/dev/null
```

That should produce something like

```
deb: bazel-out/k8-fastbuild/bin/mwp_3.14_all.deb
changes: bazel-out/k8-fastbuild/bin/mwp_3.changes
```

### How it works

show_deb_outputs.bzl is a Starlark script that must contain a function with the
name `format`, that takes a single argument. The argument is typically named
target, and is a configured Bazel target, as you might have access to while
writing a custom rule. We can inspect its providers and print them in a useful
way.

For pkg_deb, there are two files, the .deb file and the .changes, and both are
passed along in the rule's OutputGroupInfo provider. This snippet below prints
them.

```
def format(target):
  provider_map = providers(target)
  output_group_info = provider_map["OutputGroupInfo"]
  # Extract the depset of files for the .deb output and return the first
  deb_file = output_group_info.deb.to_list()[0]
  # Do the same for the changes file.
  changes_file = output_group_info.deb.to_list()[0]
  # Return a nicely formatted string showing their paths
  return '\n'.join([
      'deb: ' + deb_file.path,
      'changes: ' + changes_file.path,
      ])
```

A full explanation of why this works is beyond the scope of this example. It
requires some knowledge of how to write custom Bazel rules. See the Bazel
documenation for more information.
