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

licenses(["notice"])

load("@rules_pkg//:mappings.bzl", "pkg_attributes", "pkg_filegroup", "pkg_files", "pkg_mkdirs", "strip_prefix")
load("@rules_pkg//:pkg.bzl", "pkg_tar", "pkg_zip")

pkg_files(
    name = "share_doc",
    srcs = [
        "//docs",
    ],
    # Required, but why?: see #354
    strip_prefix = strip_prefix.from_pkg(),
    # Where it should be in the final package
    prefix = "usr/share/doc/foo",
)

pkg_zip(
    name = "foo_zip",
    srcs = [
        ":share_doc",
    ],
)

pkg_filegroup(
    name = "manpages",
    srcs = [
        "//src/client:manpages",
        "//src/server:manpages",
    ],
    prefix = "/usr/share",
)

pkg_tar(
    name = "foo_tar",
    srcs = [
        "README.txt",
        ":manpages",
        ":share_doc",
        "//resources/l10n:all",
        "//src/client:arch",
        "//src/server:arch",
    ],
)
