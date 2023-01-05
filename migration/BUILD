# Copyright 2023 The Bazel Authors. All rights reserved.
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

load("@rules_python//python:defs.bzl", "py_binary")
load("@rules_python//python:pip.bzl", "compile_pip_requirements")
load("@rules_pkg_migration_deps//:requirements.bzl", "requirement")

filegroup(
    name = "standard_package",
    srcs = glob([
      "*.py"
    ] + [
        "BUILD",
        "migration_deps.txt",
        "migration_deps_lock.txt",
    ]),
    visibility = ["//distro:__pkg__"],
)

py_binary(
    name = "strip_prefix",
    srcs = ["migrate_strip_prefix.py"],
    main = "migrate_strip_prefix.py",
    deps = [requirement("libcst")],
)

compile_pip_requirements(
    name = "requirements",
    requirements_in = "migration_deps.txt",
    requirements_txt = "migration_deps_lock.txt",
)
