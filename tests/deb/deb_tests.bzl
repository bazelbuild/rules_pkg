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
"""Helpers for pkg_deb tests."""

load("@bazel_skylib//lib:unittest.bzl", "analysistest", "asserts")

def assert_contains(env, expected, got, msg = None):
    """Asserts that the given `expected` occurs in a set of things.

    Args:
      env: The test environment returned by `unittest.begin`.
      expected: An expected value.
      go: The actual set returned by some computation.
      msg: An optional message that will be printed that describes the failure.
          If omitted, a default will be used.
    """
    if expected in got:
        return
    expectation_msg = "Expected %s in (%s)" % (expected, got)
    if msg:
        full_msg = "%s (%s)" % (msg, expectation_msg)
    else:
        full_msg = expectation_msg
    fail(env, full_msg)

def _package_naming_test_impl(ctx):
    env = analysistest.begin(ctx)
    target_under_test = analysistest.target_under_test(env)

    ogi = target_under_test[OutputGroupInfo]

    deb_path = ogi.deb.to_list()[0].path

    # Test that the .changes file is computed correctly
    changes_path = ogi.changes.to_list()[0].path
    expected_changes_path = deb_path[0:-3] + "changes"
    asserts.equals(
        env,
        changes_path,
        expected_changes_path,
        "Changes file does not have the correct name",
    )

    # Is the generated file name what we expect
    if ctx.attr.expected_name:
        asserts.equals(
            env,
            ctx.attr.expected_name,
            deb_path.split("/")[-1],  # basename(path)
            "Deb package file name is not correct",
        )
    return analysistest.end(env)

package_naming_test = analysistest.make(
    _package_naming_test_impl,
    attrs = {
        "expected_name": attr.string(),
    },
)

def _all_files_in_default_info_impl(ctx):
    env = analysistest.begin(ctx)
    target_under_test = analysistest.target_under_test(env)
    di = target_under_test[DefaultInfo]
    files = di.files.to_list()
    file_names = ",".join([f.basename for f in files])
    asserts.equals(
        env,
        3,
        len(files),
        file_names,
    )

    expect_output = target_under_test.label.name + ".deb"
    assert_contains(
        env,
        expect_output,
        file_names,
    )

    expect_output = ctx.attr.expected_basename + ".deb"
    assert_contains(
        env,
        expect_output,
        file_names,
    )

    expect_output = ctx.attr.expected_basename + ".changes"
    assert_contains(
        env,
        expect_output,
        file_names,
    )

    return analysistest.end(env)

all_files_in_default_info_test = analysistest.make(
    _all_files_in_default_info_impl,
    attrs = {
        "expected_basename": attr.string(),
    },
)
