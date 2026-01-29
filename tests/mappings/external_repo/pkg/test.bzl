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

"""Tests for file mapping routines in pkg/mappings.bzl.

Test implementation copied from pkg/mappings.bzl

"""

load("@//pkg:mappings.bzl", "pkg_files", "strip_prefix")
load("@//pkg:providers.bzl", "PackageFilesInfo")
load("@bazel_skylib//lib:new_sets.bzl", "sets")
load("@bazel_skylib//lib:unittest.bzl", "analysistest", "asserts")

#### BEGIN copied code

def _pkg_files_contents_test_impl(ctx):
    env = analysistest.begin(ctx)
    target_under_test = analysistest.target_under_test(env)

    expected_dests = sets.make(ctx.attr.expected_dests)
    actual_dests = sets.make(target_under_test[PackageFilesInfo].dest_src_map.keys())

    asserts.new_set_equals(env, expected_dests, actual_dests, "pkg_files dests do not match expectations")

    return analysistest.end(env)

pkg_files_contents_test = analysistest.make(
    _pkg_files_contents_test_impl,
    attrs = {
        # Other attributes can be tested here, but the most important one is the
        # destinations.
        "expected_dests": attr.string_list(
            mandatory = True,
        ),
        # attrs are always passed through unchanged (and maybe rejected)
    },
)

#### END copied code

# Called from the rules_pkg tests
def test_referencing_remote_file(name):
    """Test external package file references with automatic path preservation.

    This test suite verifies that `pkg_files` automatically preserves package-relative paths when referencing files from
    an external package. Nested tests should produce the same result.

    Args:
        name: Name of the generated test suite, also base name for generated test targets.
    """
    tests = [
        # The prefix in rules_pkg.  Why yes, this is knotty
        struct(name = "{}_strip_prefix_from_root".format(name), strip_prefix = strip_prefix.from_root("tests")),
        # ... which corresponds to stripping all directory components up to the package
        struct(name = "{}_strip_prefix_from_pkg".format(name), strip_prefix = strip_prefix.from_pkg()),
        # ... and should also match the default behavior
        struct(name = "{}_auto_strip_prefix".format(name), strip_prefix = None),
    ]

    for test in tests:
        pkg_files(
            name = "{}_g".format(test.name),
            prefix = "usr/share",
            srcs = ["@//tests:loremipsum_txt"],
            strip_prefix = test.strip_prefix,
            tags = ["manual"],
        )

        pkg_files_contents_test(
            name = test.name,
            target_under_test = ":{}_g".format(test.name),
            expected_dests = ["usr/share/testdata/loremipsum.txt"],
        )

    native.test_suite(name = name, tests = [":{}".format(test.name) for test in tests])
