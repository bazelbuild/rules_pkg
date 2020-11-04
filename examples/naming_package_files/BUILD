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
# -*- coding: utf-8 -*-

licenses(["notice"])

load("@rules_pkg//:pkg.bzl", "pkg_tar")

load(":my_package_name.bzl", "my_package_naming")

config_setting(
    name = "special_build",
    values = {"define": "SPECIAL=1"},
)

# Exposes the value of the compilation mode to the package naming.
my_package_naming(
    name = "my_naming_vars",

    # An explicit value.
    # This technique can be useful if you need to create packages in many
    # different formats but have not decided on the final naming yet. You
    # can use a placeholder and change it on one location.
    # 
    product_name = "RulesPkgExamples",

    # Use a config_setting flag to specify part of the package name.
    # In this example, we define the config_setting based on a command line
    # flag. Example
    #     bazel build :my_tar
    #     bazel build :my_tar --define=SPECIAL=1
    special_build = select({
        ":special_build": "-IsSpecial",
        "//conditions:default": "",
    }),
)

# Try building with various flag combinations to show the abilities
#   bazel build :my_tar -c dbg --define=SPECIAL=1
pkg_tar(
    name = "my_tar",
    srcs = [
        ":BUILD",
    ],
    package_file_name = "{product_name}-{target_cpu}-{compilation_mode}{special_build}.tar",
    package_variables = ":my_naming_vars",
)
