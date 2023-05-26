# Copyright 2023 The Bazel Authors. All rights reserved.
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

load("@//pkg:tar.bzl", "pkg_tar")
load("@//pkg:verify_archive.bzl", "verify_archive_test")

pkg_tar(
    name = "external_archive",
    srcs = ["file.txt"],
)

verify_archive_test(
    name = "external_archive_test",
    max_size = 1,
    min_size = 1,
    must_contain = ["file.txt"],
    target = ":external_archive",
)
