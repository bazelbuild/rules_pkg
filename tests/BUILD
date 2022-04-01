# Copyright 2020 The Bazel Authors. All rights reserved.
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

load("@rules_python//python:defs.bzl", "py_test")
load("@bazel_skylib//rules:copy_file.bzl", "copy_file")
load(":my_package_name.bzl", "my_package_naming")
load(":path_test.bzl", "path_tests")
load("//pkg:deb.bzl", "pkg_deb")
load("//pkg:mappings.bzl", "pkg_attributes", "pkg_mkdirs")
load("//pkg:tar.bzl", "pkg_tar")
load("//pkg:zip.bzl", "pkg_zip")

package(default_applicable_licenses = ["//:license"])

licenses(["notice"])

exports_files(glob(["testdata/**"]))

filegroup(
    name = "loremipsum_txt",
    srcs = [
        "testdata/loremipsum.txt",
    ],
    visibility = ["//visibility:public"],
)

py_test(
    name = "archive_test",
    srcs = [
        "archive_test.py",
    ],
    data = [
        "//tests:testdata/empty.ar",
        "//tests:testdata/a_ab.ar",
        "//tests:testdata/a.ar",
        "//tests:testdata/a_b_ab.ar",
        "//tests:testdata/a_b.ar",
        "//tests:testdata/ab.ar",
        "//tests:testdata/b.ar",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//pkg/private:archive",
        "@bazel_tools//tools/python/runfiles",
    ],
)

py_test(
    name = "path_test",
    srcs = ["path_test.py"],
    data = ["//pkg:path.bzl"],
    python_version = "PY3",
    srcs_version = "PY3",
)

py_test(
    name = "helpers_test",
    srcs = ["helpers_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//pkg/private:helpers",
    ],
)

#
# Tests for package_file_name
#
my_package_naming(
    name = "my_package_variables",
    label = "some_value",
)

pkg_tar(
    name = "test_tar_naming",
    srcs = [
        ":BUILD",
    ],
    package_file_name = "test_naming_{label}.tar",
    package_variables = ":my_package_variables",
)

pkg_deb(
    name = "test_deb_naming",
    data = ":test_tar_naming",
    description = "desc",
    maintainer = "someone@somewhere.com",
    package = "some_name",
    package_file_name = "test_naming_{label}.deb",
    package_variables = ":my_package_variables",
    version = "1",
)

pkg_zip(
    name = "test_zip_naming",
    srcs = [
        ":BUILD",
    ],
    package_file_name = "test_naming_{label}.zip",
    package_variables = ":my_package_variables",
)

# This just proves that we would create the files via package_file_name rather
# than the default out file.
sh_test(
    name = "package_naming_aggregate_test",
    srcs = ["package_naming_aggregate_test.sh"],
    data = [
        ":test_deb_naming",
        ":test_tar_naming",
        ":test_zip_naming",
    ],
)

pkg_tar(
    name = "stamped_tar",
    srcs = ["BUILD"],
    stamp = 1,
)

pkg_zip(
    name = "stamped_zip",
    srcs = ["BUILD"],
    stamp = 1,
)

# Note that this only tests that stamping works. Other tests cover the case
# of archive members having the default, epoch, time stamp.
py_test(
    name = "stamp_test",
    srcs = [
        "stamp_test.py",
    ],
    data = [
        "stamped_tar.tar",
        "stamped_zip.zip",
    ],
    python_version = "PY3",
    deps = [
        "@bazel_tools//tools/python/runfiles",
    ],
)

path_tests(name = "path_tests")
