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
"""tar.bzl's prebuilt bsdtar binaries, as toolchains of //toolchains/bsdtar:bsdtar_toolchain_type."""

load("@tar.bzl//tar/toolchain:platforms.bzl", "BSDTAR_PLATFORMS")

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

# Platforms of the bsd_tar_toolchains_* repositories MODULE.bazel brings in.
[
    toolchain(
        name = platform,
        exec_compatible_with = BSDTAR_PLATFORMS[platform].compatible_with,
        toolchain = "@bsd_tar_toolchains_%s//:bsdtar_toolchain" % platform,
        toolchain_type = "//toolchains/bsdtar:bsdtar_toolchain_type",
    )
    for platform in [
        "darwin_amd64",
        "darwin_arm64",
        "linux_amd64",
        "linux_arm64",
        "windows_amd64",
        "windows_arm64",
    ]
]
