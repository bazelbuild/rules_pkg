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

load(
    ":mappings_test.bzl",
     "manifest_golden_test",
     "mappings_analysis_tests",
     "mappings_unit_tests",
)
load(":mappings_external_repo_test.bzl", "mappings_external_repo_analysis_tests")
load(
    "//:mappings.bzl",
    "pkg_attributes",
    "pkg_filegroup",
    "pkg_files",
    "pkg_mkdirs",
    "pkg_mklink",
    "strip_prefix",
)
load("//tests/util:defs.bzl", "write_content_manifest")
load("@rules_python//python:defs.bzl", "py_test")

py_library(
    name = "manifest_test_lib",
    srcs = ["manifest_test_lib.py"],
    srcs_version = "PY3",
    deps = [
        "@bazel_tools//tools/python/runfiles",
    ],
)

mappings_unit_tests()

mappings_analysis_tests()

mappings_external_repo_analysis_tests()

pkg_mkdirs(
    name = "dirs",
    attributes = pkg_attributes(
        group = "bar",
        mode = "711",
        user = "foo",
    ),
    dirs = [
        "foodir",
    ],
)

pkg_files(
    name = "files",
    srcs = [
        "mappings_test.bzl",
    ],
)

write_content_manifest(
    name = "all",
    srcs = [
        "BUILD",
        ":dirs",
        ":files",
    ],
)

manifest_golden_test(
    name = "all_test",
    target = "all",
    expected = "all.manifest.golden",
)

#
# Unicode handling tests
#
pkg_files(
    name = "utf8_files",
    srcs = [
        "//tests/testdata/utf8:files",
    ],
    strip_prefix = strip_prefix.from_pkg(),
)

write_content_manifest(
    name = "utf8",
    srcs = [
        ":utf8_files",
    ],
)

manifest_golden_test(
    name = "utf8_manifest_test",
    target = "utf8",
    expected = "utf8_manifest.golden",
)
