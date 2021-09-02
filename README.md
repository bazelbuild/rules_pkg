# Bazel package building

Bazel rules for building tar, zip, deb, and rpm for packages.

Use rules-pkg-discuss@googlegroups.com for discussion.

CI:
[![Build status](https://badge.buildkite.com/e12f23186aa579f1e20fcb612a22cd799239c3134bc38e1aff.svg)](https://buildkite.com/bazel/rules-pkg)

## Basic rules

### Package building rules

*   [pkg](https://github.com/bazelbuild/rules_pkg/tree/main/pkg) - Rules for
    building packages of various types.
*   [examples](https://github.com/bazelbuild/rules_pkg/tree/main/examples) -
    Cookbook examples for using the rules.

As of Bazel 4.x, Bazel uses this rule set for packaging its distribution. Bazel
still contains a limited version of `pkg_tar` but its feature set is frozen.
Any new capabilities will be added here.

### For developers

patching.md
README.md

*   [Contributor information](CONTRIBUTING.md) (including contributor license agreements)
*   [Patch process](patching.md)
*   [Coding guidelines](developers.md) and other developer information
