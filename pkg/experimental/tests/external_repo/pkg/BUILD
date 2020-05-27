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

load("@rules_pkg//experimental:pkg_filegroup.bzl", "make_strip_prefix", "pkg_filegroup")
load("test.bzl", "test_referencing_remote_file")

licenses(["notice"])

package(default_visibility = ["//visibility:public"])

exports_files(
    glob(["**"]),
    visibility = ["//visibility:public"],
)

sh_binary(
    name = "script",
    srcs = ["dir/extproj.sh"],
    visibility = ["//visibility:public"],
)

pkg_filegroup(
    name = "extproj_script_pfg",
    srcs = ["dir/extproj.sh"],
    prefix = "usr/bin",
    strip_prefix = make_strip_prefix(from_pkg = ""),
)

test_referencing_remote_file(
    name = "pfg_local_file_in_extrepo",
)
