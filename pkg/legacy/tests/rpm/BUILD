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
# -*- coding: utf-8 -*-

load("//pkg:rpm.bzl", "pkg_rpm")

pkg_rpm(
    name = "test-rpm",
    # TODO(aiuto): Replace the use of these .ar files with something more
    # usefule to testing rpm builds.
    data = [
        "//tests:testdata/a.ar",
        "//tests:testdata/a_ab.ar",
        "//tests:testdata/a_b.ar",
        "//tests:testdata/a_b_ab.ar",
        "//tests:testdata/ab.ar",
        "//tests:testdata/b.ar",
        "//tests:testdata/config",
    ],
    debug = 1,
    release = "0",
    spec_file = "test_rpm.spec",
    version = "1",
)
