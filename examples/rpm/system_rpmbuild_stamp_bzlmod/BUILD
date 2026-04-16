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

# Example: use stamp = 1 to substitute workspace status variables in the
# release tag.  Build with `bazel build --stamp :test-rpm-stamped` to embed
# the build timestamp.

load("@rules_pkg//pkg:mappings.bzl", "pkg_files")
load("@rules_pkg//pkg:rpm.bzl", "pkg_rpm")

pkg_files(
    name = "rpm_content",
    srcs = [
        "BUILD",
        "MODULE.bazel",
        "README.md",
    ],
    prefix = "/usr/share",
)

pkg_rpm(
    name = "test-rpm-stamped",
    srcs = ["rpm_content"],
    architecture = "noarch",
    description = "placeholder 2",
    license = "Apache License, v2.0",
    release = "0.{BUILD_TIMESTAMP}",
    stamp = 1,
    summary = "rules_pkg example RPM with stamped release",
    version = "1",
)
