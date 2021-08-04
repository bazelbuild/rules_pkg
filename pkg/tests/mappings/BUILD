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

load(":mappings_test.bzl", "mappings_analysis_tests", "mappings_unit_tests")
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

# TODO(aiuto): This rule and the small srcs should be generated from just the
# pair of write_content_manifest name and the golden file name.
# We could even inline the golden data into a string which gets parsed as
# json and written out.
py_test(
    name = "all_test",
    srcs = [
        "all_test.py",
    ],
    data = [
        "all.manifest.golden",
        ":all.manifest",
    ],
    python_version = "PY3",
    deps = [
        ":manifest_test_lib",
    ],
)

py_library(
    name = "manifest_test_lib",
    srcs = ["manifest_test_lib.py"],
    srcs_version = "PY3",
    deps = [
        "@bazel_tools//tools/python/runfiles",
    ],
)
