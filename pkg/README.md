# rules_pkg - Archive building rules

-   [Release Notes](#notes)
-   [Overview](#overview)
-   [Roadmap](#roadmap)
-   [Reference](docs/reference.md)
-   [Examples](/examples/readme.md)

<a name="notes"></a>
## Release Notes

Version 1.0.0 or later (including all currently in-development code) requires
Bazel 4.0.0 or later.

<a name="overview"></a>
## Overview

These build rules are used for building various packaging such as tarball
and debian package.

<a name="workspace-setup"></a>
### WORKSPACE setup

See [releases](https://github.com/bazelbuild/rules_pkg/releases) for the release
specific notes.

If you want to use `pkg_rpm()` (either from `rpm.bzl` or `legacy/rpm.bzl`)
you must instantiate a toolchain to provide the `rpmbuild` tool.  Add this to
WORKSPACE to use one installed on your system:

```python
# Find rpmbuild provided on your system.
load("@rules_pkg//toolchains:rpmbuild_configure.bzl", "find_system_rpmbuild")
find_system_rpmbuild(name = "rules_pkg_rpmbuild")
```

<a name="basic-example"></a>
### Basic Example

This example is a simplification of the debian packaging of Bazel:

```python
load("@rules_pkg//:pkg.bzl", "pkg_tar", "pkg_deb")


pkg_tar(
    name = "bazel-bin",
    strip_prefix = "/src",
    package_dir = "/usr/bin",
    srcs = ["//src:bazel"],
    mode = "0755",
)

pkg_tar(
    name = "bazel-tools",
    strip_prefix = "/",
    package_dir = "/usr/share/lib/bazel/tools",
    srcs = ["//tools:package-srcs"],
    mode = "0644",
)

pkg_tar(
    name = "debian-data",
    extension = "tar.gz",
    deps = [
        ":bazel-bin",
        ":bazel-tools",
    ],
)

pkg_deb(
    name = "bazel-debian",
    architecture = "amd64",
    built_using = "unzip (6.0.1)",
    data = ":debian-data",
    depends = [
        "zlib1g-dev",
        "unzip",
    ],
    description_file = "debian/description",
    homepage = "http://bazel.build",
    maintainer = "The Bazel Authors <bazel-dev@googlegroups.com>",
    package = "bazel",
    version = "0.1.1",
)
```

Here, the Debian package is built from three `pkg_tar` targets:

 - `bazel-bin` creates a tarball with the main binary (mode `0755`) in
   `/usr/bin`,
 - `bazel-tools` create a tarball with the base workspace (mode `0644`) to
   `/usr/share/bazel/tools` ; the `modes` attribute let us specifies executable
   files,
 - `debian-data` creates a gzip-compressed tarball that merge the three previous
   tarballs.

`debian-data` is then used for the data content of the debian archive created by
`pkg_deb`.

<a name="roadmap"></a>
## Roadmap

 - Add a `pkg_filegroup` rule to facilitate mapping Bazel targets into an the
   folder layout required by the archive.
 - Support assigning owners and modes to specific files in the archive.
 - Improve RPM support
 - Improve DEB support
