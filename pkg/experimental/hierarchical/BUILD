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

# NOTE: this is a conceptual example, and is unlikely to work as-is

load(":pkg_filegroup.bzl", "pkg_file", "pkg_filegroup")

# NOTE: does not exist
load(":rpm.bzl", "pkg_rpm")

pkg_rpm(
    name = "rpm",
    data = [
        ":package_root",
    ],
    rpm_name = "hello-rpm",
)

pkg_filegroup(
    name = "package_root",
    data = [
        ":etc",
        ":usr",
    ],
    prefix = "/",
)

pkg_filegroup(
    name = "usr",
    data = [
        ":usr_bin",
    ],
    prefix = "usr",
)

pkg_filegroup(
    name = "usr_bin",
    data = [
        pkg_file(
            "hello_bin",
            srcs = ["//path/to:hello"],
            attr = {"unix": [
                "0755",
                "root",
                "root",
            ]},
        ),
    ],
    prefix = "bin",
)

pkg_filegroup(
    name = "etc",
    data = [
        pkg_file(
            "hello_config",
            srcs = ["//path/to:hello.conf"],
        ),
    ],
    prefix = "etc",
)
