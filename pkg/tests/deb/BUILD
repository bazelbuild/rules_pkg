# -*- coding: utf-8 -*-
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

# Tests for pkg_deb specific behavior

load("//:mappings.bzl", "pkg_mklink")
load("//:pkg.bzl", "pkg_deb", "pkg_tar")
load("//tests:my_package_name.bzl", "my_package_naming")
load("@rules_python//python:defs.bzl", "py_test")

genrule(
    name = "generate_files",
    outs = [
        "etc/nsswitch.conf",
        "usr/titi",
    ],
    cmd = "for i in $(OUTS); do echo 1 >$$i; done",
)

my_package_naming(
    name = "my_package_variables",
    label = "some_value",
)

pkg_mklink(
    name = "java_link",
    src = "/path/to/bin/java",
    dest = "usr/bin/java",
)

pkg_tar(
    name = "tar_input",
    srcs = [
        ":etc/nsswitch.conf",
        ":java_link",
        ":usr/titi",
    ],
    extension = "tar.gz",
    mode = "0644",
    modes = {"usr/titi": "0755"},
    owner = "42.24",
    ownername = "titi.tata",
    ownernames = {"etc/nsswitch.conf": "tata.titi"},
    owners = {"etc/nsswitch.conf": "24.42"},
    package_dir = "/",
    strip_prefix = ".",
)

pkg_deb(
    name = "test-deb",
    breaks = ["oldbrokenpkg"],
    built_using = "some_test_data (0.1.2)",
    conffiles = [
        "/etc/nsswitch.conf",
        "/etc/other",
    ],
    config = "//tests:testdata/config",
    data = ":tar_input",
    depends = [
        "dep1",
        "dep2",
    ],
    description = "toto ®, Й, ק ,م, ๗, あ, 叶, 葉, 말, ü and é",
    distribution = "trusty",
    maintainer = "soméone@somewhere.com",
    package = "titi",
    preinst = "//tests:testdata/deb_preinst",
    provides = ["hello"],
    replaces = ["oldpkg"],
    templates = "//tests:testdata/templates",
    triggers = "//tests:testdata/deb_triggers",
    urgency = "low",
    version = "test",
)

py_test(
    name = "pkg_deb_test",
    size = "medium",
    srcs = [
        "pkg_deb_test.py",
    ],
    data = [
        # The target includes both the .deb and .changes files in DefaultInfo
        ":test-deb",
    ],
    python_version = "PY3",
    deps = [
        "//private:archive",
        "@bazel_tools//tools/python/runfiles",
    ],
)
