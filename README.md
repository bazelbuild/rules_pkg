# Bazel package building & fetching rules

Bazel rules for packaging and fetching (for Debian and other distribution
channels).

Use rules-pkg-discuss@googlegroups.com for discussion.

CI:
[![Build status](https://badge.buildkite.com/e12f23186aa579f1e20fcb612a22cd799239c3134bc38e1aff.svg)](https://buildkite.com/bazel/rules-pkg)

## Basic rules

### Package building rules

*   [pkg](https://github.com/bazelbuild/rules_pkg/tree/master/pkg) - Rules for
    building packages of various types.

We are currently in the process of migrating the
[Bazel packaging rules](https://docs.bazel.build/versions/master/be/pkg.html)
from Bazel to this repo. Tracking issue:
https://github.com/bazelbuild/bazel/issues/8489.

Bazel now uses this rule set for packaging it's distribution. It still contains
a vestigial early version of these rules, but those will be removed in a future
release.

### debian specific rules

*   [deb_packages](https://github.com/bazelbuild/rules_pkg/tree/master/deb_packages#deb_packages) -
    WORKSPACE rule to fetch deb files from Debain style mirror servers

*   [update_deb_packages](https://github.com/bazelbuild/rules_pkg/tree/master/deb_packages/tools#deb_packages) -
    update the hash and path of files mentioned in `deb_packages` rules

#### Background

The `deb_package` rules originated in the
[distroless](https://github.com/GoogleCloudPlatform/distroless) project as well
as discussions about the goal of that project and are intended as a way to
retrieve bundled software packages from various places.

The initial scope is currently targeting `Debian` style distributions, because
the Bazel [docker rules](https://github.com/bazelbuild/rules_docker) allow
optional `deb` and `tar` files to be included in their container images. That
work was done in December 2017.
