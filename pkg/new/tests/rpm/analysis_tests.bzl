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

"""Tests for RPM generation analysis"""

load("@bazel_skylib//lib:unittest.bzl", "analysistest", "asserts", "unittest")
load("//new:rpm.bzl", "pkg_rpm")
load("//:providers.bzl", "PackageDirsInfo", "PackageFilegroupInfo", "PackageFilesInfo", "PackageSymlinkInfo")
load(
    "//:mappings.bzl",
    "pkg_attributes",
    "pkg_filegroup",
    "pkg_files",
    "pkg_mkdirs",
    "pkg_mklink",
    "strip_prefix",
)

# Generic negative test boilerplate
#
# TODO: create an internal test library containing this function, and maybe the second one too
def _generic_neg_test_impl(ctx):
    env = analysistest.begin(ctx)

    asserts.expect_failure(env, ctx.attr.reason)

    return analysistest.end(env)

generic_neg_test = analysistest.make(
    _generic_neg_test_impl,
    attrs = {
        "reason": attr.string(
            default = "",
        ),
    },
    expect_failure = True,
)

def _generic_base_case_test_impl(ctx):
    env = analysistest.begin(ctx)

    # Nothing here intentionally, this is simply an attempt to verify successful
    # analysis.

    return analysistest.end(env)

generic_base_case_test = analysistest.make(
    _generic_base_case_test_impl,
    attrs = {},
)

def _declare_pkg_rpm(name, srcs_ungrouped, tags = None, **kwargs):
    pfg_name = "{}_pfg".format(name)
    _tags = tags or ["manual"]

    pkg_filegroup(
        name = pfg_name,
        srcs = srcs_ungrouped,
        tags = _tags,
    )

    pkg_rpm(
        name = name,
        srcs = [":" + pfg_name],
        version = "1.0",
        release = "1",
        license = "N/A",
        summary = "A test",
        description = "very much a test",
        tags = _tags,
        **kwargs
    )

def _declare_conflicts_test(name, srcs, **kwargs):
    rpm_name = name + "_rpm"
    _declare_pkg_rpm(
        name = rpm_name,
        srcs_ungrouped = srcs,
        tags = ["manual"],
    )

    generic_neg_test(
        name = name,
        target_under_test = ":" + rpm_name,
    )

def _test_conflicting_inputs(name):
    # The test here is to confirm if pkg_rpm rejects conflicting inputs
    #
    # The structure of the code is such that it's only necessary to test any one
    # packaged item conflicts with all others; order is irrelevant.
    #
    # So, we test how everything would conflict with a "file" entry
    pkg_files(
        name = "{}_file_base".format(name),
        srcs = ["foo"],
        tags = ["manual"],
    )

    _declare_pkg_rpm(
        name = name + "_base",
        srcs_ungrouped = [":{}_file_base".format(name)],
    )

    generic_base_case_test(
        name = name + "_base_case_passes_analysis",
        target_under_test = ":" + name + "_base",
    )

    ##################################################
    # file vs conflicting file
    ##################################################

    pkg_files(
        name = "{}_file_conflict".format(name),
        srcs = ["foo"],
        tags = ["manual"],
    )

    _declare_conflicts_test(
        name = name + "_conflict_with_file",
        srcs = [
            ":{}_file_base".format(name),
            ":{}_file_conflict".format(name),
        ],
    )

    ##################################################
    # file vs conflicting dir
    ##################################################

    pkg_mkdirs(
        name = "{}_dir_conflict".format(name),
        dirs = ["foo"],
        tags = ["manual"],
    )

    _declare_conflicts_test(
        name = name + "_conflict_with_dir",
        srcs = [
            ":{}_file_base".format(name),
            ":{}_dir_conflict".format(name),
        ],
    )

    ##################################################
    # file vs conflicting symbolic link
    ##################################################

    pkg_mklink(
        name = "{}_symlink_conflict".format(name),
        dest = "foo",
        src = "bar",
        tags = ["manual"],
    )

    _declare_conflicts_test(
        name = name + "_conflict_with_symlink",
        srcs = [
            ":{}_file_base".format(name),
            ":{}_symlink_conflict".format(name),
        ],
    )

    native.test_suite(
        name = name,
        tests = [":{}_{}".format(name, test_name)
                 for test_name in
                 [
                     "base_case_passes_analysis",
                     "conflict_with_file",
                     "conflict_with_dir",
                     "conflict_with_symlink",
                 ]
        ],
    )


def analysis_tests(name, **kwargs):
    # Need to test:
    #
    # - Mutual exclusivity of certain options (low)
    #
    _test_conflicting_inputs(name = name + "_conflicting_inputs")
    native.test_suite(
        name = name,
        tests = [
            name + "_conflicting_inputs"
        ],
    )
