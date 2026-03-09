# Copyright 2026 The Bazel Authors. All rights reserved.
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
"""rules_pkg internal code.

All interfaces are subject to change at any time.
"""

load("@rules_python//python:py_binary.bzl", "py_binary")
load("@rules_python//python:py_library.bzl", "py_library")
load("@rules_python//python:py_test.bzl", "py_test")

package(
    default_package_metadata = ["//:license"],
    default_visibility = ["//visibility:public"],
)

filegroup(
    name = "standard_package",
    srcs = [
        "BUILD",
    ] + glob([
        "*.py",
    ]),
    visibility = [
        "//distro:__pkg__",
        "//doc_build:__pkg__",
    ],
)

py_binary(
    name = "cpio-ls",
    srcs = [
        "cpio-ls.py",
    ],
    deps = [
        "//contrib/tools/lib:cpio",
    ],
)

py_binary(
    name = "rpm2cpio",
    srcs = [
        "rpm2cpio.py",
    ],
    deps = [
        "//contrib/tools/lib:rpm_file",
    ],
)

py_binary(
    name = "rpm_build",
    srcs = [
        "rpm_build.py",
    ],
    deps = [
        "//contrib/tools/lib:rpm_writer",
    ],
)

py_binary(
    name = "rpm_info",
    srcs = [
        "rpm_info.py",
    ],
    deps = [
        "//contrib/tools/lib:cpio",
        "//contrib/tools/lib:in_process_pipe",
        "//contrib/tools/lib:rpm_file",
    ],
)

py_binary(
    name = "tree_size_compare",
    srcs = [
        "tree_size_compare.py",
    ],
    deps = [
        "//contrib/tools/lib:deb_reader",
        "//contrib/tools/lib:fs_reader",
        "//contrib/tools/lib:rpm_reader",
        "//contrib/tools/lib:saved_tree",
        "//contrib/tools/lib:tar_reader",
        "//contrib/tools/lib:tree_reader",
    ],
)

py_library(
    name = "tree_size_compare_lib",
    srcs = ["tree_size_compare.py"],
    deps = [
        "//contrib/tools/lib:deb_reader",
        "//contrib/tools/lib:fs_reader",
        "//contrib/tools/lib:rpm_reader",
        "//contrib/tools/lib:saved_tree",
        "//contrib/tools/lib:tar_reader",
        "//contrib/tools/lib:tree_reader",
    ],
)

py_test(
    name = "readers_test",
    srcs = ["readers_test.py"],
    data = [
        "//contrib/tools/testdata:reference_tar",
        "//contrib/tools/testdata:reference_tar_gz",
        "//contrib/tools/testdata:reference_tar_xz",
        "//contrib/tools/testdata:test_deb",
    ],
    deps = [
        "//contrib/tools/lib:deb_reader",
        "//contrib/tools/lib:in_process_pipe",
        "//contrib/tools/lib:saved_tree",
        "//contrib/tools/lib:tar_reader",
        "@rules_python//python/runfiles",
    ],
)

py_test(
    name = "compare_test",
    srcs = ["compare_test.py"],
    data = [
        "//contrib/tools/testdata:different_mode_tar",
        "//contrib/tools/testdata:different_owner_tar",
        "//contrib/tools/testdata:different_symlink_tar",
        "//contrib/tools/testdata:extra_file_tar",
        "//contrib/tools/testdata:modified_tar",
        "//contrib/tools/testdata:reference_tar",
    ],
    deps = [
        ":tree_size_compare_lib",
        "//contrib/tools/lib:tar_reader",
        "@rules_python//python/runfiles",
    ],
)
