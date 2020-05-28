# Tools to help with managing rules in this repository

## update_deb_packages

A tool to update the path and SHA256 hash of packages referred to by `deb_packages` rules in WORKSPACE files.
(Essentially `apt-get update && apt-get upgrade` for `deb_packages` rules in the current WORKSPACE.)

[(Documentation here)](https://github.com/bazelbuild/rules_pkg/tree/master/deb_packages/tools/update_deb_packages)
