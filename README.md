# Bazel package fetching rules

Bazel rules for packaging (for Debian and other distribution channels). Repo
initialized December 2017.

Travis CI
:---:
[![Build Status](https://travis-ci.org/bazelbuild/rules_pkg.svg?branch=master)](https://travis-ci.org/bazelbuild/rules_pkg)

## Basic Rules

### WORKSPACE Rules

* [deb_packages](https://github.com/bazelbuild/rules_pkg/tree/master/deb_packages#deb_packages) - fetch deb files from Debain style mirror servers

## Helper tools

* [update_deb_packages](https://github.com/bazelbuild/rules_pkg/tree/master/tools/deb_packages#deb_packages) - update the hash and path of files mentioned in `deb_packages` rules


## Background

These rules originated in the [distroless](https://github.com/GoogleCloudPlatform/distroless)
project as well as discussions about the goal of that project and are intended as a way to retrieve
bundled software packages from various places.

The initial scope is currently targeting `Debian` style distributions, because the Bazel
[docker rules](https://github.com/bazelbuild/rules_docker) allow optional `deb` and `tar`
files to be included in their container images.

Currently these rules are focused on retrieving already built packages from repositories,
not creating them as artifacts (e.g. like the Bazel
[packaging rules](https://docs.bazel.build/versions/master/be/pkg.html)).
In the future it is also planned to consolidate rules that are creating package files in this
repository, to have a central place to look for package related rules for use in Bazel builds.
