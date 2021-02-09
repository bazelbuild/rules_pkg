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

load("@rules_pkg//:pkg.bzl", "pkg_deb", "pkg_tar")
load(":package_upload.bzl", "debian_upload")
load(":my_package_name.bzl", "basic_naming", "label_from_command_line", "names_from_toolchains")

config_setting(
    name = "special_build",
    values = {"define": "SPECIAL=1"},
)

# Exposes the value of the compilation mode to the package naming.
basic_naming(
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
    #     bazel build :example1
    #     bazel build :example1 --define=SPECIAL=1
    special_build = select({
        ":special_build": "-IsSpecial",
        "//conditions:default": "",
    }),
)

# Try building with various flag combinations to explore.
#   bazel build :example1
#   bazel build :example1 -c dbg
#   bazel build :example1 -define=SPECIAL=1
#   bazel build :example1 -c dbg --define=SPECIAL=1
pkg_tar(
    name = "example1",
    srcs = [
        ":BUILD",
    ],
    package_file_name = "example1-{product_name}-{target_cpu}-{compilation_mode}{special_build}.tar",
    package_variables = ":my_naming_vars",
)

#
# names_from_toolchains() extracts variables from the CC toolchain.
#
names_from_toolchains(
    name = "toolchain_vars",
)

pkg_tar(
    name = "example2",
    srcs = [
        ":BUILD",
    ],
    package_file_name = "example2-{cc_cpu}-{compiler}-{compilation_mode}.tar",
    package_variables = ":toolchain_vars",
)

#
# Demonstrate how the .changes file defaults based on package_file_name.
#
pkg_deb(
    name = "a_deb_package",
    data = ":example1",
    description = "what it does",
    maintainer = "someone@somewhere.com",
    package = "foo_tools",
    # Note: We could not know target_cpu at the time I write this rule.
    package_file_name = "foo_tools-1-{target_cpu}.deb",
    package_variables = ":my_naming_vars",
    version = "1",
)

# This does not actually build anything. It writes a skelaton of a script that
# could upload the .deb and .changes pair.  You should see something like
# $ cat bazel-bin/upload.sh
# # Uploading foo_tools-1-k8
# gsutil cp bazel-out/k8-fastbuild/bin/foo_tools-1-k8.deb gs://my_mirror/foo_tools-1-k8.deb
# gsutil cp bazel-out/k8-fastbuild/bin/foo_tools-1-k8.changes gs://my_mirror/foo_tools-1-k8.changes
debian_upload(
    name = "upload",
    out = "upload.sh",
    host = "my_mirror",
    # Refer to the target label, without having to know the final file name.
    package = ":a_deb_package",
)

#
# Demonstrate how we can use a value from the command line in a package name.
#
# bazel build --//:label_from_command_line=bar  :tarball_that_needs_a_name
# ls bazel-bin/foo-bar.tar
label_from_command_line(
    name = "label_from_command_line",
    build_setting_default = "@set_me@",
)

pkg_tar(
    name = "tarball_that_needs_a_name",
    srcs = [
        ":BUILD",
    ],
    package_file_name = "foo-{label}.tar",
    package_variables = ":label_from_command_line",
)
