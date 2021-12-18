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

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

# Find rpmbuild if it exists.
load("@rules_pkg//toolchains:rpmbuild_configure.bzl", "find_system_rpmbuild")

find_system_rpmbuild(
    name = "rules_pkg_rpmbuild",
    verbose = True,
)

# Needed for making our release notes
load("@rules_pkg//toolchains/git:git_configure.bzl", "experimental_find_system_git")

experimental_find_system_git(
    name = "rules_pkg_git",
    verbose = True,
)

http_archive(
    name = "bazel_stardoc",
    sha256 = "36b8d6c2260068b9ff82faea2f7add164bf3436eac9ba3ec14809f335346d66a",
    strip_prefix = "stardoc-0.4.0",
    url = "https://github.com/bazelbuild/stardoc/archive/0.4.0.zip",
)

load("@bazel_stardoc//:setup.bzl", "stardoc_repositories")

stardoc_repositories()

# TODO(nacl): remove this when the "new" framework is ready.
local_repository(
    name = "experimental_test_external_repo",
    path = "pkg/experimental/tests/external_repo",
)

local_repository(
    name = "mappings_test_external_repo",
    path = "tests/mappings/external_repo",
)

load("@rules_python//python:pip.bzl", "pip_parse")

pip_parse(
    name = "migration_deps",
    requirements_lock = "//migration:migration_deps_lock.txt",
)

load("@migration_deps//:requirements.bzl", "install_deps")
install_deps()
