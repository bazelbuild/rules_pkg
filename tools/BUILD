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
        "//tools/lib:cpio",
    ],
)

py_binary(
    name = "rpm2cpio",
    srcs = [
        "rpm2cpio.py",
    ],
    deps = [
        "//tools/lib:rpm_file",
    ],
)

py_binary(
    name = "rpm_build",
    srcs = [
        "rpm_build.py",
    ],
    deps = [
        "//tools/lib:rpm_writer",
    ],
)

py_binary(
    name = "rpm_info",
    srcs = [
        "rpm_info.py",
    ],
    deps = [
        "//tools/lib:cpio",
        "//tools/lib:in_process_pipe",
        "//tools/lib:rpm_file",
    ],
)

py_binary(
    name = "tree_size_compare",
    srcs = [
        "tree_size_compare.py",
    ],
    deps = [
        "//tools/lib:deb_reader",
        "//tools/lib:fs_reader",
        "//tools/lib:rpm_reader",
        "//tools/lib:saved_tree",
        "//tools/lib:tar_reader",
        "//tools/lib:tree_reader",
    ],
)

py_library(
    name = "tree_size_compare_lib",
    srcs = ["tree_size_compare.py"],
    deps = [
        "//tools/lib:deb_reader",
        "//tools/lib:fs_reader",
        "//tools/lib:rpm_reader",
        "//tools/lib:saved_tree",
        "//tools/lib:tar_reader",
        "//tools/lib:tree_reader",
    ],
)

py_test(
    name = "readers_test",
    srcs = ["readers_test.py"],
    data = [
        "//tools/testdata:reference_tar",
        "//tools/testdata:reference_tar_gz",
        "//tools/testdata:reference_tar_xz",
        "//tools/testdata:test_deb",
    ],
    deps = [
        "//tools/lib:deb_reader",
        "//tools/lib:in_process_pipe",
        "//tools/lib:saved_tree",
        "//tools/lib:tar_reader",
        "@rules_python//python/runfiles",
    ],
)

py_test(
    name = "compare_test",
    srcs = ["compare_test.py"],
    data = [
        "//tools/testdata:different_mode_tar",
        "//tools/testdata:different_owner_tar",
        "//tools/testdata:different_symlink_tar",
        "//tools/testdata:extra_file_tar",
        "//tools/testdata:modified_tar",
        "//tools/testdata:reference_tar",
    ],
    deps = [
        ":tree_size_compare_lib",
        "//tools/lib:tar_reader",
        "@rules_python//python/runfiles",
    ],
)
