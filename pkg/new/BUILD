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

load("//:mappings.bzl", "pkg_filegroup", "pkg_files")
load(":rpm.bzl", "pkg_rpm")

# TODO(nacl): this needs to be exported to the package.  Will look into this
# once we know how we're going to be laying everything out.

exports_files(
    glob([
        "*.bzl",
    ]) + [
        "template.spec.in",
    ],
    visibility = ["//visibility:public"],
)

pkg_files(
    name = "artifacts",
    srcs = [":template.spec.in"],
)

pkg_filegroup(
    name = "usr_share_artifacts",
    srcs = [":artifacts"],
)

pkg_rpm(
    name = "example",
    srcs = [":usr_share_artifacts"],
    description = "Other example!",
    license = "N/A",
    release = "1",
    summary = "Example!",
    version = "1.0",
)
