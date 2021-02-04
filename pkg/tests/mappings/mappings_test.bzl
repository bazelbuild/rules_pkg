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

"""Tests for file mapping routines in pkg/mappings.bzl"""

load("@bazel_skylib//lib:new_sets.bzl", "sets")
load("@bazel_skylib//lib:unittest.bzl", "analysistest", "asserts", "unittest")
load(
    "//:mappings.bzl",
    "pkg_attributes",
    "pkg_files",
    "pkg_mkdirs",
    "strip_prefix",
)
load("//:providers.bzl", "PackageDirsInfo", "PackageFilesInfo")

def _pkg_files_contents_test_impl(ctx):
    env = analysistest.begin(ctx)
    target_under_test = analysistest.target_under_test(env)

    expected_dests = sets.make(ctx.attr.expected_dests)
    actual_dests = sets.make(target_under_test[PackageFilesInfo].dest_src_map.keys())

    asserts.new_set_equals(env, expected_dests, actual_dests, "pkg_files dests do not match expectations")

    # Simple equality checks for the others, if specified
    if ctx.attr.expected_attributes:
        asserts.equals(
            env,
            json.decode(ctx.attr.expected_attributes),
            target_under_test[PackageFilesInfo].attributes,
            "pkg_files attributes do not match expectations",
        )

    return analysistest.end(env)

pkg_files_contents_test = analysistest.make(
    _pkg_files_contents_test_impl,
    attrs = {
        # Other attributes can be tested here, but the most important one is the
        # destinations.
        "expected_dests": attr.string_list(
            mandatory = True,
        ),
        "expected_attributes": attr.string(),
    },
)

# Generic negative test boilerplate
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

def _test_pkg_files_contents():
    # Test stripping when no arguments are provided (same as strip_prefix.files_only())
    pkg_files(
        name = "pf_no_strip_prefix_g",
        srcs = ["testdata/hello.txt"],
        attributes = pkg_attributes(
            mode = "0644",
            user = "foo",
            group = "bar",
            # kwargs begins here
            foo = "bar",
        ),
        tags = ["manual"],
    )

    pkg_files_contents_test(
        name = "pf_no_strip_prefix",
        target_under_test = ":pf_no_strip_prefix_g",
        expected_dests = ["hello.txt"],
        expected_attributes = pkg_attributes(
            mode = "0644",
            user = "foo",
            group = "bar",
            foo = "bar",
        ),
    )

    # And now, files_only = True
    pkg_files(
        name = "pf_files_only_g",
        srcs = ["testdata/hello.txt"],
        strip_prefix = strip_prefix.files_only(),
        tags = ["manual"],
    )

    pkg_files_contents_test(
        name = "pf_files_only",
        target_under_test = ":pf_files_only_g",
        expected_dests = ["hello.txt"],
    )

    # Used in the following tests
    #
    # Note that since the pkg_files rule is never actually used in anything
    # other than this test, nonexistent_script can be included with no ill effects. :P
    native.sh_binary(
        name = "testdata/test_script",
        srcs = ["testdata/nonexistent_script.sh"],
        tags = ["manual"],
    )

    # Test stripping from the package root
    pkg_files(
        name = "pf_from_pkg_g",
        srcs = [
            "testdata/hello.txt",
            ":testdata/test_script",
        ],
        strip_prefix = strip_prefix.from_pkg("testdata/"),
        tags = ["manual"],
    )

    pkg_files_contents_test(
        name = "pf_strip_testdata_from_pkg",
        target_under_test = ":pf_from_pkg_g",
        expected_dests = [
            # Static file
            "hello.txt",
            # The script itself
            "nonexistent_script.sh",
            # The generated target output, in this case, a symlink
            "test_script",
        ],
    )

    # Test the stripping from root.
    #
    # In this case, the components to be stripped are taken relative to the root
    # of the package.  Local and generated files should have the same prefix in
    # all cases.

    pkg_files(
        name = "pf_from_root_g",
        srcs = [":testdata/test_script"],
        strip_prefix = strip_prefix.from_root("tests/mappings"),
        tags = ["manual"],
    )

    pkg_files_contents_test(
        name = "pf_strip_prefix_from_root",
        target_under_test = ":pf_from_root_g",
        expected_dests = [
            # The script itself
            "testdata/nonexistent_script.sh",
            # The generated target output, in this case, a symlink
            "testdata/test_script",
        ],
    )

    # Test that pkg_files rejects cases where two sources resolve to the same
    # destination.
    pkg_files(
        name = "pf_destination_collision_invalid_g",
        srcs = ["foo", "bar/foo"],
        tags = ["manual"],
    )
    generic_neg_test(
        name = "pf_destination_collision_invalid",
        target_under_test = ":pf_destination_collision_invalid_g",
    )

    # Test strip_prefix when it can't complete the strip operation as requested.
    pkg_files(
        name = "pf_strip_prefix_from_package_invalid_g",
        srcs = ["foo/foo", "bar/foo"],
        strip_prefix = strip_prefix.from_pkg("bar"),
        tags = ["manual"],
    )
    generic_neg_test(
        name = "pf_strip_prefix_from_package_invalid",
        target_under_test = ":pf_strip_prefix_from_package_invalid_g",
    )

    # Ditto, except strip from the root.
    pkg_files(
        name = "pf_strip_prefix_from_root_invalid_g",
        srcs = ["foo", "bar"],
        strip_prefix = strip_prefix.from_root("not/the/root"),
        tags = ["manual"],
    )
    generic_neg_test(
        name = "pf_strip_prefix_from_root_invalid",
        target_under_test = ":pf_strip_prefix_from_root_invalid_g",
    )

def _test_pkg_files_exclusions():
    # Normal filegroup, used in all of the below tests
    #
    # Needs to be here to test the distinction between files and label inputs to
    # "excludes".  This, admittedly, may be unnecessary.
    native.filegroup(
        name = "test_base_fg",
        srcs = [
            "testdata/config",
            "testdata/hello.txt",
        ],
    )

    # Tests to exclude from the case where stripping is done up to filenames
    pkg_files(
        name = "pf_exclude_by_label_strip_all_g",
        srcs = [":test_base_fg"],
        excludes = ["//tests/mappings:testdata/config"],
        tags = ["manual"],
    )
    pkg_files_contents_test(
        name = "pf_exclude_by_label_strip_all",
        target_under_test = ":pf_exclude_by_label_strip_all_g",
        expected_dests = ["hello.txt"],
    )

    pkg_files(
        name = "pf_exclude_by_filename_strip_all_g",
        srcs = [":test_base_fg"],
        excludes = ["testdata/config"],
        tags = ["manual"],
    )
    pkg_files_contents_test(
        name = "pf_exclude_by_filename_strip_all",
        target_under_test = ":pf_exclude_by_filename_strip_all_g",
        expected_dests = ["hello.txt"],
    )

    # Tests to exclude from the case where stripping is done from the package root
    pkg_files(
        name = "pf_exclude_by_label_strip_from_pkg_g",
        srcs = [":test_base_fg"],
        excludes = ["//tests/mappings:testdata/config"],
        strip_prefix = strip_prefix.from_pkg("testdata"),
        tags = ["manual"],
    )
    pkg_files_contents_test(
        name = "pf_exclude_by_label_strip_from_pkg",
        target_under_test = ":pf_exclude_by_label_strip_from_pkg_g",
        expected_dests = ["hello.txt"],
    )

    pkg_files(
        name = "pf_exclude_by_filename_strip_from_pkg_g",
        srcs = [":test_base_fg"],
        excludes = ["testdata/config"],
        strip_prefix = strip_prefix.from_pkg("testdata"),
        tags = ["manual"],
    )
    pkg_files_contents_test(
        name = "pf_exclude_by_filename_strip_from_pkg",
        target_under_test = ":pf_exclude_by_filename_strip_from_pkg_g",
        expected_dests = ["hello.txt"],
    )

    # Tests to exclude from the case where stripping is done from the root
    pkg_files(
        name = "pf_exclude_by_label_strip_from_root_g",
        srcs = [":test_base_fg"],
        excludes = ["//tests/mappings:testdata/config"],
        strip_prefix = strip_prefix.from_root("tests/mappings"),
        tags = ["manual"],
    )
    pkg_files_contents_test(
        name = "pf_exclude_by_label_strip_from_root",
        target_under_test = ":pf_exclude_by_label_strip_from_root_g",
        expected_dests = ["testdata/hello.txt"],
    )

    pkg_files(
        name = "pf_exclude_by_filename_strip_from_root_g",
        srcs = [":test_base_fg"],
        excludes = ["testdata/config"],
        strip_prefix = strip_prefix.from_root("tests/mappings"),
        tags = ["manual"],
    )
    pkg_files_contents_test(
        name = "pf_exclude_by_filename_strip_from_root",
        target_under_test = ":pf_exclude_by_filename_strip_from_root_g",
        expected_dests = ["testdata/hello.txt"],
    )

# Tests involving external repositories
def _test_pkg_files_extrepo():
    # From external repo root, basenames only
    pkg_files(
        name = "pf_extrepo_strip_all_g",
        srcs = ["@mappings_test_external_repo//pkg:dir/script"],
        tags = ["manual"],
    )
    pkg_files_contents_test(
        name = "pf_extrepo_strip_all",
        target_under_test = ":pf_extrepo_strip_all_g",
        expected_dests = ["extproj.sh", "script"],
    )

    # From external repo root, relative to the "pkg" package
    pkg_files(
        name = "pf_extrepo_strip_from_pkg_g",
        srcs = ["@mappings_test_external_repo//pkg:dir/script"],
        strip_prefix = strip_prefix.from_pkg("dir"),
        tags = ["manual"],
    )
    pkg_files_contents_test(
        name = "pf_extrepo_strip_from_pkg",
        target_under_test = ":pf_extrepo_strip_from_pkg_g",
        expected_dests = [
            "extproj.sh",
            "script",
        ],
    )

    # From external repo root, relative to the "pkg" directory
    pkg_files(
        name = "pf_extrepo_strip_from_root_g",
        srcs = ["@mappings_test_external_repo//pkg:dir/script"],
        strip_prefix = strip_prefix.from_root("pkg"),
        tags = ["manual"],
    )
    pkg_files_contents_test(
        name = "pf_extrepo_strip_from_root",
        target_under_test = ":pf_extrepo_strip_from_root_g",
        expected_dests = ["dir/extproj.sh", "dir/script"],
    )

    native.filegroup(
        name = "extrepo_test_fg",
        srcs = ["@mappings_test_external_repo//pkg:dir/extproj.sh"],
    )

    # Test the case when a have a pkg_files that targets a local filegroup
    # that has files in an external repo.
    pkg_files(
        name = "pf_extrepo_filegroup_strip_from_pkg_g",
        srcs = [":extrepo_test_fg"],
        # Files within filegroups should be considered relative to their
        # destination paths.
        strip_prefix = strip_prefix.from_pkg(""),
    )
    pkg_files_contents_test(
        name = "pf_extrepo_filegroup_strip_from_pkg",
        target_under_test = ":pf_extrepo_filegroup_strip_from_pkg_g",
        expected_dests = ["dir/extproj.sh"],
    )

    # Ditto, except strip from the workspace root instead
    pkg_files(
        name = "pf_extrepo_filegroup_strip_from_root_g",
        srcs = [":extrepo_test_fg"],
        # Files within filegroups should be considered relative to their
        # destination paths.
        strip_prefix = strip_prefix.from_root("pkg"),
    )
    pkg_files_contents_test(
        name = "pf_extrepo_filegroup_strip_from_root",
        target_under_test = ":pf_extrepo_filegroup_strip_from_root_g",
        expected_dests = ["dir/extproj.sh"],
    )

    # Reference a pkg_files in @mappings_test_external_repo
    pkg_files_contents_test(
        name = "pf_pkg_files_in_extrepo",
        target_under_test = "@mappings_test_external_repo//pkg:extproj_script_pf",
        expected_dests = ["usr/bin/dir/extproj.sh"],
    )

def _test_pkg_files_rename():
    pkg_files(
        name = "pf_rename_multiple_g",
        srcs = [
            "testdata/hello.txt",
            "testdata/loremipsum.txt",
        ],
        prefix = "usr",
        renames = {
            "testdata/hello.txt": "share/goodbye.txt",
            "testdata/loremipsum.txt": "doc/dolorsitamet.txt",
        },
        tags = ["manual"],
    )
    pkg_files_contents_test(
        name = "pf_rename_multiple",
        target_under_test = ":pf_rename_multiple_g",
        expected_dests = [
            "usr/share/goodbye.txt",
            "usr/doc/dolorsitamet.txt",
        ],
    )

    # Used in the following tests
    #
    # Note that since the pkg_files rule is never actually used in anything
    # other than this test, nonexistent_script can be included with no ill
    # effects. :P
    native.sh_binary(
        name = "test_script_rename",
        srcs = ["testdata/nonexistent_script.sh"],
        tags = ["manual"],
    )

    # test_script_rename produces multiple outputs.  Thus, this test should
    # fail, as pkg_files can't figure out what should actually be mapped to
    # the output destination.
    pkg_files(
        name = "pf_rename_rule_with_multiple_outputs_g",
        srcs = ["test_script_rename"],
        renames = {
            ":test_script_rename": "still_nonexistent_script",
        },
        tags = ["manual"],
    )
    generic_neg_test(
        name = "pf_rename_rule_with_multiple_outputs",
        target_under_test = ":pf_rename_rule_with_multiple_outputs_g",
    )

    # Fail because we tried to install a file that wasn't mentioned in the deps
    # list
    pkg_files(
        name = "pf_rename_single_missing_value_g",
        srcs = ["testdata/hello.txt"],
        prefix = "usr",
        renames = {
            "nonexistent_script": "nonexistent_output_location",
        },
        tags = ["manual"],
    )
    generic_neg_test(
        name = "pf_rename_single_missing_value",
        target_under_test = ":pf_rename_single_missing_value_g",
    )

    # Ditto, except for exclusions
    pkg_files(
        name = "pf_rename_single_excluded_value_g",
        srcs = [
            "testdata/hello.txt",
            "testdata/loremipsum.txt",
        ],
        prefix = "usr",
        excludes = [
            "testdata/hello.txt",
        ],
        renames = {
            "testdata/hello.txt": "share/goodbye.txt",
        },
        tags = ["manual"],
    )
    generic_neg_test(
        name = "pf_rename_single_excluded_value",
        target_under_test = ":pf_rename_single_excluded_value_g",
    )

    # Test whether or not destination collisions are detected after renaming.
    pkg_files(
        name = "pf_rename_destination_collision_g",
        srcs = [
            "foo",
            "bar",
        ],
        renames = {"foo": "bar"},
        tags = ["manual"],
    )
    generic_neg_test(
        name = "pf_rename_destination_collision",
        target_under_test = ":pf_rename_destination_collision_g",
    )

##########
# Test pkg_mkdirs
##########

def _pkg_mkdirs_contents_test_impl(ctx):
    env = analysistest.begin(ctx)
    target_under_test = analysistest.target_under_test(env)

    expected_dirs = sets.make(ctx.attr.expected_dirs)
    actual_dirs = sets.make(target_under_test[PackageDirsInfo].dirs)

    asserts.new_set_equals(env, expected_dirs, actual_dirs, "pkg_mkdirs dirs do not match expectations")

    # Simple equality checks for the others
    if ctx.attr.expected_attributes != None:
        asserts.equals(
            env,
            json.decode(ctx.attr.expected_attributes),
            target_under_test[PackageDirsInfo].attributes,
            "pkg_mkdir attributes do not match expectations",
        )

    return analysistest.end(env)

pkg_mkdirs_contents_test = analysistest.make(
    _pkg_mkdirs_contents_test_impl,
    attrs = {
        "expected_attributes": attr.string(),
        "expected_dirs": attr.string_list(
            mandatory = True,
        ),
    },
)

def _test_pkg_mkdirs():
    # Reasonable base case
    pkg_mkdirs(
        name = "pkg_mkdirs_base_g",
        dirs = ["foo/bar", "baz"],
        attributes = pkg_attributes(
            mode = "0711",
            user = "root",
            group = "sudo",
        ),
        tags = ["manual"],
    )
    pkg_mkdirs_contents_test(
        name = "pkg_mkdirs_base",
        target_under_test = "pkg_mkdirs_base_g",
        expected_dirs = ["foo/bar", "baz"],
        expected_attributes = pkg_attributes(
            mode = "0711",
            user = "root",
            group = "sudo",
        ),
    )

##########
# Test strip_prefix pseudo-module
##########

def _strip_prefix_test_impl(ctx):
    env = unittest.begin(ctx)
    asserts.equals(env, ".", strip_prefix.files_only())
    asserts.equals(env, "path", strip_prefix.from_pkg("path"))
    asserts.equals(env, "path", strip_prefix.from_pkg("/path"))
    asserts.equals(env, "/path", strip_prefix.from_root("path"))
    asserts.equals(env, "/path", strip_prefix.from_root("/path"))
    return unittest.end(env)

strip_prefix_test = unittest.make(_strip_prefix_test_impl)

def mappings_analysis_tests():
    """Declare mappings.bzl analysis tests"""
    _test_pkg_files_contents()
    _test_pkg_files_exclusions()
    _test_pkg_files_extrepo()
    _test_pkg_files_rename()
    _test_pkg_mkdirs()

    native.test_suite(
        name = "pkg_files_analysis_tests",
        # We should find a way to get rid of this test list; it would be nice if
        # it could be derived from something else...
        tests = [
            # buildifier: don't sort
            # Simple tests
            ":pf_no_strip_prefix",
            ":pf_files_only",
            ":pf_strip_testdata_from_pkg",
            ":pf_strip_prefix_from_root",
            # Tests involving excluded files
            ":pf_exclude_by_label_strip_all",
            ":pf_exclude_by_filename_strip_all",
            ":pf_exclude_by_label_strip_from_pkg",
            ":pf_exclude_by_filename_strip_from_pkg",
            ":pf_exclude_by_label_strip_from_root",
            ":pf_exclude_by_filename_strip_from_root",
            # Negative tests
            ":pf_destination_collision_invalid",
            ":pf_strip_prefix_from_package_invalid",
            ":pf_strip_prefix_from_root_invalid",
            # Tests involving external repositories
            ":pf_extrepo_strip_all",
            ":pf_extrepo_strip_from_pkg",
            ":pf_extrepo_strip_from_root",
            ":pf_extrepo_filegroup_strip_from_pkg",
            ":pf_extrepo_filegroup_strip_from_root",
            ":pf_pkg_files_in_extrepo",
            # This one fits into the same category, but can't be aliased, apparently.
            #
            # The main purpose behind it is to verify cases wherein we build a
            # file, but then have it consumed by some remote package.
            "@mappings_test_external_repo//pkg:pf_local_file_in_extrepo",
            # Tests involving file renaming
            ":pf_rename_multiple",
            ":pf_rename_rule_with_multiple_outputs",
            ":pf_rename_single_missing_value",
            ":pf_rename_single_excluded_value",
            # Tests involving pkg_mkdirs
            ":pkg_mkdirs_base",
        ],
    )

def mappings_unit_tests():
    unittest.suite(
        "mappings_unit_tests",
        strip_prefix_test,
    )
