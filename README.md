# Bazel package building

Bazel rules for building tar, zip, deb, and rpm for packages.

Use rules-pkg-discuss@googlegroups.com for discussion.

CI:
[![Build status](https://badge.buildkite.com/e12f23186aa579f1e20fcb612a22cd799239c3134bc38e1aff.svg)](https://buildkite.com/bazel/rules-pkg)

## Basic rules

### Package building rules

*   [pkg](https://github.com/bazelbuild/rules_pkg/tree/main/pkg) - Rules for
    building packages of various types.

Bazel now uses this rule set for packaging its distribution. Bazel
still contains a limited version of `pkg_tar` but its feature set is frozen.
Any new capabilities will be added here.
