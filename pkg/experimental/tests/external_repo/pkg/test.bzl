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

"""Tests for file mapping routines in pkg/experimental/pkg_filegroup.bzl.

Test implementation copied from pkg/experimental/tests/pkg_filegroup_test.bzl

"""

load("@bazel_skylib//lib:new_sets.bzl", "sets")
load("@bazel_skylib//lib:unittest.bzl", "analysistest", "asserts")
load("@//experimental:pkg_filegroup.bzl", "PackageFileInfo", "make_strip_prefix", "pkg_filegroup")

#### BEGIN copied code

def _pkg_filegroup_contents_test_impl(ctx):
    env = analysistest.begin(ctx)
    target_under_test = analysistest.target_under_test(env)

    expected_dests = sets.make(ctx.attr.expected_dests)
    actual_dests = sets.make(target_under_test[PackageFileInfo].dests)

    asserts.new_set_equals(env, expected_dests, actual_dests, "pkg_filegroup dests do not match expectations")

    return analysistest.end(env)

pkg_filegroup_contents_test = analysistest.make(
    _pkg_filegroup_contents_test_impl,
    attrs = {
        #"expected_srcs" : attr.label_list(),
        "expected_dests": attr.string_list(
            mandatory = True,
        ),
        # attrs/section are always passed
        # through unchanged (and maybe
        # rejected)
    },
)
#### END copied code

# Called from the rules_pkg tests
def test_referencing_remote_file(name):
    pkg_filegroup(
        name = "{}_g".format(name),
        prefix = "usr/share",
        srcs = ["@//tests:loremipsum_txt"],
        # The prefix in rules_pkg.  Why yes, this is knotty
        strip_prefix = make_strip_prefix(from_root = "tests"),
    )

    pkg_filegroup_contents_test(
        name = name,
        target_under_test = ":{}_g".format(name),
        expected_dests = ["usr/share/testdata/loremipsum.txt"],
    )
