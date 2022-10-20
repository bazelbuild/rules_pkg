# Copyright 2021 The Bazel Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

workspace(name = "rules_pkg")

load("@rules_pkg//pkg:deps.bzl", "rules_pkg_dependencies")

rules_pkg_dependencies()

load("@bazel_skylib//:workspace.bzl", "bazel_skylib_workspace")

bazel_skylib_workspace()

### INTERNAL ONLY - lines after this are not included in the release packaging.
#
# Include dependencies which are only needed for development here.

# Used to test invoking rules with targets in an external repo.
local_repository(
    name = "mappings_test_external_repo",
    path = "tests/mappings/external_repo",
)

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
    name = "platforms",
    urls = [
        "https://mirror.bazel.build/github.com/bazelbuild/platforms/releases/download/0.0.5/platforms-0.0.5.tar.gz",
        "https://github.com/bazelbuild/platforms/releases/download/0.0.5/platforms-0.0.5.tar.gz",
    ],
    sha256 = "379113459b0feaf6bfbb584a91874c065078aa673222846ac765f86661c27407",
)

# Find rpmbuild if it exists.
load("@rules_pkg//toolchains/rpm:rpmbuild_configure.bzl", "find_system_rpmbuild")

find_system_rpmbuild(
    name = "rules_pkg_rpmbuild",
    verbose = False,
)

# Needed for making our release notes
load("@rules_pkg//toolchains/git:git_configure.bzl", "experimental_find_system_git")

experimental_find_system_git(
    name = "rules_pkg_git",
    verbose = False,
)

http_archive(
    name = "bazel_stardoc",
    sha256 = "c9794dcc8026a30ff67cf7cf91ebe245ca294b20b071845d12c192afe243ad72",
    urls = [
        "https://mirror.bazel.build/github.com/bazelbuild/stardoc/releases/download/0.5.0/stardoc-0.5.0.tar.gz",
        "https://github.com/bazelbuild/stardoc/releases/download/0.5.0/stardoc-0.5.0.tar.gz",
    ],
)

load("@bazel_stardoc//:setup.bzl", "stardoc_repositories")

stardoc_repositories()
