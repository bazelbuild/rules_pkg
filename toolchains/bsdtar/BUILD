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
"""Optional toolchain making pkg_tar write archives with bsdtar instead of Python tarfile.

Type: @rules_pkg//toolchains/bsdtar:bsdtar_toolchain_type

Toolchains of this type provide the ToolchainInfo of tar.bzl's `tar_toolchain`
(@tar.bzl//tar/toolchain:toolchain.bzl). pkg_tar falls back to Python tarfile
when none resolves.

Toolchains:
- prebuilt:all: tar.bzl's prebuilt bsdtar binaries, which pkg_tar uses once
  registered from MODULE.bazel:

    register_toolchains("@rules_pkg//toolchains/bsdtar/prebuilt:all")
"""

package(default_applicable_licenses = ["//:license"])

filegroup(
    name = "standard_package",
    srcs = glob([
        "*",
    ]),
    visibility = [
        "//distro:__pkg__",
        "//doc_build:__pkg__",
    ],
)

toolchain_type(
    name = "bsdtar_toolchain_type",
    visibility = ["//visibility:public"],
)
