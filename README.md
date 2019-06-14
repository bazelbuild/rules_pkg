# Bazel package building & fetching rules

Bazel rules for packaging and fetching (for Debian and other distribution channels).

There is currently no distinct discussion group for these rules. Use bazel-dev@googlegroups.com.


Travis CI
:---:
[![Build Status](https://travis-ci.org/bazelbuild/rules_pkg.svg?branch=master)](https://travis-ci.org/bazelbuild/rules_pkg)

## Basic Rules

### Package Building Rules

* [pkg](https://github.com/bazelbuild/rules_pkg/pkg) - Rules for building
  packages of various types.


### WORKSPACE Rules

* [deb_packages](https://github.com/bazelbuild/rules_pkg/tree/master/deb_packages#deb_packages) - fetch deb files from Debain style mirror servers

## Helper tools

* [update_deb_packages](https://github.com/bazelbuild/rules_pkg/tree/master/tools/deb_packages#deb_packages) - update the hash and path of files mentioned in `deb_packages` rules


## Background

These rules originated in the
[distroless](https://github.com/GoogleCloudPlatform/distroless) project
as well as discussions about the goal of that project and are intended
as a way to retrieve bundled software packages from various places.

The initial scope is currently targeting `Debian`
style distributions, because the Bazel [docker
rules](https://github.com/bazelbuild/rules_docker) allow optional `deb`
and `tar` files to be included in their container images.  That work
was done in December 2017.

We are currently (June 2019) in the process of migrating the
[Bazel packaging rules](https://docs.bazel.build/versions/master/be/pkg.html)
from Bazel to this repo.  Tracking issue: https://github.com/bazelbuild/bazel/issues/8489.

Plan
-   DONE: slight refactor and fixup of existing package fetching rules.
-   DONE: copy rules from https://github.com/bazelbuild/bazel/tools/build_defs/pkg.
-   DONE: refactor this repo so that package fetching rules have distinct WORKSPACE
    requirements.
-   DONE: get them working
-   integrated with federation CI.
-   migrate rules shipped with Bazel to this rule set.
-   migrate Bazel distribution packaging to use this rule set.
-   innovate wildly.

The last 4 steps may overlap in time.
