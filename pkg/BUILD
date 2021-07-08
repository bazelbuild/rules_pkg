# Copyright 2019 The Bazel Authors. All rights reserved.
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

# -*- coding: utf-8 -*-
load("@rules_python//python:defs.bzl", "py_binary", "py_library")

licenses(["notice"])

exports_files(
    glob([
        "*.bzl",
    ]),
    visibility = ["//visibility:public"],
)

constraint_setting(name = "not_compatible_setting")

constraint_value(
    name = "not_compatible",
    constraint_setting = ":not_compatible_setting",
    visibility = ["//visibility:public"],
)

filegroup(
    name = "standard_package",
    srcs = glob([
        "*.bzl",
        "*.py",
        "*.md",
    ]) + [
        "BUILD",
        "LICENSE",
        "//legacy:standard_package",
        "//rpm:standard_package",
    ],
    visibility = ["//distro:__pkg__"],
)

exports_files(
    ["WORKSPACE"],
    visibility = ["//visibility:public"],
)

# Used by pkg_rpm in rpm.bzl.
py_binary(
    name = "make_rpm",
    srcs = ["make_rpm.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    # TODO(aiuto): Enable this for bazel 4.x
    #target_compatible_with = select({
    #    "//toolchains:have_rpmbuild": [],
    #    "//conditions:default": [":not_compatible"],
    #}),
    visibility = ["//visibility:public"],
    deps = [
        "//private:archive",
        ":make_rpm_lib",
    ],
)

py_library(
    name = "make_rpm_lib",
    srcs = ["make_rpm.py"],
    srcs_version = "PY3",
    visibility = [
        "//experimental:__subpackages__",
        "//tests:__subpackages__",
    ],
    deps = [
        "//private:archive",
        "//private:helpers",
    ],
)

py_binary(
    name = "filter_directory",
    srcs = ["filter_directory.py"],
    python_version = "PY3",
    visibility = ["//visibility:public"],
)
