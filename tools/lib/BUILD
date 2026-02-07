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

load("@rules_python//python:py_library.bzl", "py_library")

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

py_library(
    name = "cpio",
    srcs = [
        "cpio.py",
    ],
    deps = [":tree_reader"],
)

py_library(
    name = "deb_reader",
    srcs = [
        "deb_reader.py",
    ],
    deps = [":tree_reader"],
)

py_library(
    name = "fs_reader",
    srcs = [
        "fs_reader.py",
    ],
    deps = [":tree_reader"],
)

py_library(
    name = "in_process_pipe",
    srcs = [
        "in_process_pipe.py",
    ],
)

py_library(
    name = "rpm_file",
    srcs = [
        "rpm_file.py",
    ],
)

py_library(
    name = "rpm_reader",
    srcs = [
        "rpm_reader.py",
    ],
    deps = [
        ":cpio",
        ":in_process_pipe",
        ":rpm_file",
        ":tree_reader",
    ],
)

py_library(
    name = "saved_tree",
    srcs = [
        "saved_tree.py",
    ],
    deps = [":tree_reader"],
)

py_library(
    name = "tar_reader",
    srcs = [
        "tar_reader.py",
    ],
    deps = [":tree_reader"],
)

py_library(
    name = "tree_reader",
    srcs = [
        "tree_reader.py",
    ],
)
