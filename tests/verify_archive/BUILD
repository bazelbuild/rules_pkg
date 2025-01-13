# Copyright 2025 The Bazel Authors. All rights reserved.
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
# -*- coding: utf-8 -*-
"""Tests for verify_archive."""

load("//pkg:tar.bzl", "pkg_tar")
load("//pkg:verify_archive.bzl", "verify_archive_test")

# Test data

pkg_tar(
    name = "loremipsum_tar",
    srcs = [
        "//tests:loremipsum_txt",
    ],
)

# Test cases

verify_archive_test(
    name = "test_size_is_allowed",
    size = "small",
    target = ":loremipsum_tar",
)

verify_archive_test(
    name = "test_testonly_is_allowed",
    testonly = True,
    target = ":loremipsum_tar",
)

verify_archive_test(
    name = "test_visibility_is_allowed",
    target = ":loremipsum_tar",
    visibility = ["//visibility:private"],
)
