# Copyright 2019 The Bazel Authors. All rights reserved.
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

"""Tests for file mapping routines in pkg/genpkg.bzl.

Test implementation copied from pkg/tests/genpkg_test.bzl

"""

load("@bazel_skylib//lib:new_sets.bzl", "sets")
load("@bazel_skylib//lib:unittest.bzl", "analysistest", "asserts", "unittest")
load("@rules_pkg//:genpkg.bzl", "PackageFileInfo", "make_strip_prefix", "pkgfilegroup")

#### BEGIN copied code

def _genpkg_contents_test_impl(ctx):
    env = analysistest.begin(ctx)
    target_under_test = analysistest.target_under_test(env)

    expected_dests = sets.make(ctx.attr.expected_dests)
    actual_dests = sets.make(target_under_test[PackageFileInfo].dests)

    asserts.new_set_equals(env, expected_dests, actual_dests, "pkgfilegroup dests do not match expectations")

    return analysistest.end(env)

genpkg_contents_test = analysistest.make(
    _genpkg_contents_test_impl,
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
    pkgfilegroup(
        name = "{}_g".format(name),
        prefix = "usr/share",
        srcs = ["@rules_pkg//tests:loremipsum_txt"],
        # The prefix in rules_pkg.  Why yes, this is knotty
        strip_prefix = make_strip_prefix(from_root = "tests"),
    )

    genpkg_contents_test(
        name = name,
        target_under_test = ":{}_g".format(name),
        expected_dests = ["usr/share/testdata/loremipsum.txt"],
    )
