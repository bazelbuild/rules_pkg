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

load("//experimental/manifest:manifest.bzl", "pkg_list_manifest")
load("//experimental:rpm.bzl", "pkg_rpm")
load(":dest-first.bzl", "manifest_info")

# This is an example to demonstrate usage.  It currently does not function.  All
# rules are tagged as manual to prevent CI from becoming angry.

manifest = pkg_list_manifest(
    name = "manifest",
    default_attrs = manifest_info["default_attrs"],
    manifest = manifest_info["manifest"],
    tags = ["manual"],
)

pkg_rpm(
    name = "nonbuilding-rpm",
    data = manifest + [
        # Other pkg_filegroups and friendes here
    ],
    tags = ["manual"],
    license = "N/A",
    summary = "don't build me!",
    # ...
)
