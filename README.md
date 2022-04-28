# Bazel package building

Bazel rules for building tar, zip, deb, and rpm for packages.

Latest version: 0.7.0 [Release Notes](https://github.com/bazelbuild/rules_pkg/releases/tag/0.7.0) /
[Documentation](https://bazelbuild.github.io/rules_pkg/0.7.0/reference.html)

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

*   [Contributor information](CONTRIBUTING.md) (including contributor license agreements)
*   [Patch process](patching.md)
*   [Coding guidelines](developers.md) and other developer information

We hold an engineering status meeting on the first Monday of every month at 10am USA East coast time.
[Add to calendar](https://calendar.google.com/event?action=TEMPLATE&tmeid=MDE2ODMzazlwZnRxbWtkZG5wa2hlYjllMGVfMjAyMTA1MDNUMTUwMDAwWiBjXzUzcHBwZzFudWthZXRmb3E5NzhxaXViNmxzQGc&tmsrc=c_53pppg1nukaetfoq978qiub6ls%40group.calendar.google.com&scp=ALL) /
[meeting notes](https://docs.google.com/document/d/1wkY8ZIcrG8tlKCHzv4st-EltsdlpQENH58fguRnErWY/edit?usp=sharing)
