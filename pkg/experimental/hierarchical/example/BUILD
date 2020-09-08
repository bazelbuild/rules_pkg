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

load("//experimental/hierarchical:pkg_filegroup.bzl", "pkg_file", "pkg_filegroup", "pkg_filegroup_dump")

# NOTE: does not exist
#load("//experimental/hierarchical:rpm.bzl", "pkg_rpm")

# The RPM will be built with something like this:

#pkg_rpm(
#    name = "rpm",
#    data = [
#        ":package_root",
#    ],
#    rpm_name = "hello-rpm",
#)

pkg_filegroup_dump(
    name = "example",
    srcs = [":package_root"],
)

# "Roots" the pkg_filegroup, resulting in:
#
# /usr/bin/hello
# /usr/lib/*.lib
# /etc/hello/hello.conf
pkg_filegroup(
    name = "package_root",
    srcs = [
        ":etc",
        ":usr",
    ],
    prefix = "/",
)

# Produces usr/, followed by the contents of ":usr_bin" and ":usr_lib", which results in:
#
# usr/bin/hello
# usr/lib/*.lib
pkg_filegroup(
    name = "usr",
    srcs = [
        ":usr_bin",
        ":usr_lib",
    ],
    # Can also be empty, in which case the pkg_filegroup just represents a list
    # of mappings in the "current" directory
    prefix = "usr",
)

# Produces "bin/hello"
pkg_filegroup(
    name = "usr_bin",
    srcs = [
        pkg_file(
            "hello_bin",
            srcs = ["hello"],
            attrs = {"unix": [
                "0755",
                "root",
                "root",
            ]},
        ),
    ],
    prefix = "bin",
)

# Produces "local/lib/$LIB" for each file ending with lib in this package.
pkg_filegroup(
    name = "usr_lib",
    srcs = [
        pkg_file(
            "hello_libs",
            srcs = glob(["*.lib"]),
            attrs = {"unix": [
                "0755",
                "root",
                "root",
            ]},
        ),
    ],
    prefix = "lib",
)

# Produces "etc/hello/hello.conf".
pkg_filegroup(
    name = "etc",
    srcs = [
        pkg_file(
            # Directories are currently truncated.  This will be controlled with
            # something like "strip_prefix".
            "hello_config",
            srcs = [":etc/hello.conf"],
        ),
    ],
    prefix = "etc",
)
