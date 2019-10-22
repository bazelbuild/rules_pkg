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

"""Tests for file mapping routines in pkg/genpkg.bzl"""

load("@bazel_skylib//lib:new_sets.bzl", "sets")
load("@bazel_skylib//lib:unittest.bzl", "analysistest", "asserts", "unittest")
load("@rules_pkg//:genpkg.bzl", "PackageFileInfo", "make_strip_prefix", "pkgfilegroup")

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

# Generic negative test boilerplate
def _genpkg_neg_test_impl(ctx):
    env = analysistest.begin(ctx)
    #target_under_test = analysistest.target_under_test(env)

    asserts.expect_failure(env, ctx.attr.reason)

    return analysistest.end(env)

genpkg_neg_test = analysistest.make(
    _genpkg_neg_test_impl,
    attrs = {
        "reason": attr.string(
            default = "",
        ),
    },
    expect_failure = True,
)

def genpkg_bad_section_test(**kwargs):
    genpkg_neg_test(
        reason = "Invalid value for section",
        **kwargs
    )

def _test_genpkg_contents():
    # Test stripping when no arguments are provided (same as files_only=True)
    pkgfilegroup(
        name = "pfg_no_strip_prefix_g",
        srcs = ["testdata/hello.txt"],
        tags = ["manual"],
    )

    genpkg_contents_test(
        name = "pfg_no_strip_prefix",
        target_under_test = ":pfg_no_strip_prefix_g",
        expected_dests = ["hello.txt"],
    )

    # And now, files_only = True
    pkgfilegroup(
        name = "pfg_files_only_g",
        srcs = ["testdata/hello.txt"],
        strip_prefix = make_strip_prefix(files_only = True),
        tags = ["manual"],
    )

    genpkg_contents_test(
        name = "pfg_files_only",
        target_under_test = ":pfg_files_only_g",
        expected_dests = ["hello.txt"],
    )

    # Used in the following tests
    #
    # Note that since the pkgfilegroup rule is never actually used in anything
    # other than this test, nonexistent_script can be included with no ill effects. :P
    native.sh_binary(
        name = "test_script",
        srcs = ["testdata/nonexistent_script.sh"],
        tags = ["manual"],
    )

    # Test stripping from the package root
    pkgfilegroup(
        name = "pfg_from_pkg_g",
        srcs = [
            "testdata/hello.txt",
            ":test_script",
        ],
        strip_prefix = make_strip_prefix(from_pkg = "testdata/"),
        tags = ["manual"],
    )

    genpkg_contents_test(
        name = "pfg_strip_testdata_from_pkg",
        target_under_test = ":pfg_from_pkg_g",
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

    pkgfilegroup(
        name = "pfg_from_root_g",
        srcs = [":test_script"],
        strip_prefix = make_strip_prefix(from_root = "tests/"),
        tags = ["manual"],
    )

    genpkg_contents_test(
        name = "pfg_strip_prefix_from_root",
        target_under_test = ":pfg_from_root_g",
        expected_dests = [
            # The script itself
            "testdata/nonexistent_script.sh",
            # The generated target output, in this case, a symlink
            "test_script",
        ],
    )

def _test_genpkg_exclusions():
    # Normal filegroup, used in all of the below tests
    native.filegroup(
        name = "test_base_fg",
        srcs = [
            "testdata/config",
            "testdata/hello.txt",
        ],
    )

    # Tests to exclude from the case where stripping is done up to filenames
    pkgfilegroup(
        name = "pfg_exclude_by_label_strip_all_g",
        srcs = ["test_base_fg"],
        excludes = ["//tests:testdata/config"],
        tags = ["manual"],
    )
    genpkg_contents_test(
        name = "pfg_exclude_by_label_strip_all",
        target_under_test = ":pfg_exclude_by_label_strip_all_g",
        expected_dests = ["hello.txt"],
    )

    pkgfilegroup(
        name = "pfg_exclude_by_filename_strip_all_g",
        srcs = ["test_base_fg"],
        excludes = ["testdata/config"],
        tags = ["manual"],
    )
    genpkg_contents_test(
        name = "pfg_exclude_by_filename_strip_all",
        target_under_test = ":pfg_exclude_by_filename_strip_all_g",
        expected_dests = ["hello.txt"],
    )

    # Tests to exclude from the case where stripping is done from the package root
    pkgfilegroup(
        name = "pfg_exclude_by_label_strip_from_pkg_g",
        srcs = ["test_base_fg"],
        excludes = ["//tests:testdata/config"],
        strip_prefix = make_strip_prefix(from_pkg = "testdata"),
        tags = ["manual"],
    )
    genpkg_contents_test(
        name = "pfg_exclude_by_label_strip_from_pkg",
        target_under_test = ":pfg_exclude_by_label_strip_from_pkg_g",
        expected_dests = ["hello.txt"],
    )

    pkgfilegroup(
        name = "pfg_exclude_by_filename_strip_from_pkg_g",
        srcs = ["test_base_fg"],
        excludes = ["testdata/config"],
        strip_prefix = make_strip_prefix(from_pkg = "testdata"),
        tags = ["manual"],
    )
    genpkg_contents_test(
        name = "pfg_exclude_by_filename_strip_from_pkg",
        target_under_test = ":pfg_exclude_by_filename_strip_from_pkg_g",
        expected_dests = ["hello.txt"],
    )

    # Tests to exclude from the case where stripping is done from the root
    pkgfilegroup(
        name = "pfg_exclude_by_label_strip_from_root_g",
        srcs = ["test_base_fg"],
        excludes = ["//tests:testdata/config"],
        strip_prefix = make_strip_prefix(from_root = "tests"),
        tags = ["manual"],
    )
    genpkg_contents_test(
        name = "pfg_exclude_by_label_strip_from_root",
        target_under_test = ":pfg_exclude_by_label_strip_from_root_g",
        expected_dests = ["testdata/hello.txt"],
    )

    pkgfilegroup(
        name = "pfg_exclude_by_filename_strip_from_root_g",
        srcs = ["test_base_fg"],
        excludes = ["testdata/config"],
        strip_prefix = make_strip_prefix(from_root = "tests"),
        tags = ["manual"],
    )
    genpkg_contents_test(
        name = "pfg_exclude_by_filename_strip_from_root",
        target_under_test = ":pfg_exclude_by_filename_strip_from_root_g",
        expected_dests = ["testdata/hello.txt"],
    )

# Tests involving external repositories
def _test_genpkg_extrepo():
    # From external repo root, basenames only
    pkgfilegroup(
        name = "pfg_extrepo_strip_all_g",
        srcs = ["@test_external_repo//pkg:script"],
        tags = ["manual"],
    )
    genpkg_contents_test(
        name = "pfg_extrepo_strip_all",
        target_under_test = ":pfg_extrepo_strip_all_g",
        expected_dests = ["extproj.sh", "script"],
    )

    # From external repo root, relative to the "pkg" package
    pkgfilegroup(
        name = "pfg_extrepo_strip_from_pkg_g",
        srcs = ["@test_external_repo//pkg:script"],
        strip_prefix = make_strip_prefix(from_pkg = "dir"),
        tags = ["manual"],
    )
    genpkg_contents_test(
        name = "pfg_extrepo_strip_from_pkg",
        target_under_test = ":pfg_extrepo_strip_from_pkg_g",
        expected_dests = [
            "extproj.sh",  # "dir" is stripped
            "script",  # Nothing to strip
        ],
    )

    # From external repo root, relative to the "pkg" directory
    pkgfilegroup(
        name = "pfg_extrepo_strip_from_root_g",
        srcs = ["@test_external_repo//pkg:script"],
        strip_prefix = make_strip_prefix(from_root = "pkg"),
        tags = ["manual"],
    )
    genpkg_contents_test(
        name = "pfg_extrepo_strip_from_root",
        target_under_test = ":pfg_extrepo_strip_from_root_g",
        expected_dests = ["dir/extproj.sh", "script"],
    )

    native.filegroup(
        name = "extrepo_test_fg",
        srcs = ["@test_external_repo//pkg:dir/extproj.sh"],
    )

    # Test the case when a have a pkgfilegroup that targets a local filegroup
    # that has files in an external repo.
    pkgfilegroup(
        name = "pfg_extrepo_filegroup_strip_from_pkg_g",
        srcs = [":extrepo_test_fg"],
        # Files within filegroups should be considered relative to their
        # destination paths.
        strip_prefix = make_strip_prefix(from_pkg = ""),
    )
    genpkg_contents_test(
        name = "pfg_extrepo_filegroup_strip_from_pkg",
        target_under_test = ":pfg_extrepo_filegroup_strip_from_pkg_g",
        expected_dests = ["dir/extproj.sh"],
    )

    # Ditto, except strip from the workspace root instead
    pkgfilegroup(
        name = "pfg_extrepo_filegroup_strip_from_root_g",
        srcs = [":extrepo_test_fg"],
        # Files within filegroups should be considered relative to their
        # destination paths.
        strip_prefix = make_strip_prefix(from_root = "pkg"),
    )
    genpkg_contents_test(
        name = "pfg_extrepo_filegroup_strip_from_root",
        target_under_test = ":pfg_extrepo_filegroup_strip_from_root_g",
        expected_dests = ["dir/extproj.sh"],
    )

    # Reference a pkgfilegroup in @test_external_repo
    genpkg_contents_test(
        name = "pfg_pkgfilegroup_in_extrepo",
        target_under_test = "@test_external_repo//pkg:extproj_script_pfg",
        expected_dests = ["usr/bin/dir/extproj.sh"],
    )

def _test_genpkg_section():
    pkgfilegroup(
        name = "pfg_good_section",
        srcs = ["testdata/hello.txt"],
        section = "doc",
        tags = ["manual"],
    )

    genpkg_contents_test(
        name = "pfg_doc_section_test",
        target_under_test = ":pfg_good_section",
        expected_dests = ["hello.txt"],
    )

    pkgfilegroup(
        name = "pfg_bad_section",
        srcs = ["testdata/hello.txt"],
        section = "bad_section",
        tags = ["manual"],
    )

    genpkg_bad_section_test(
        name = "pfg_bad_section_test",
        target_under_test = ":pfg_bad_section",
    )

def _strip_prefix_test_impl(ctx):
    env = unittest.begin(ctx)
    asserts.equals(env, ".", make_strip_prefix(files_only = True))
    asserts.equals(env, "path", make_strip_prefix(from_pkg = "path"))
    asserts.equals(env, "path", make_strip_prefix(from_pkg = "path"))
    asserts.equals(env, "path", make_strip_prefix(from_pkg = "/path"))
    asserts.equals(env, "/path", make_strip_prefix(from_root = "path"))
    asserts.equals(env, "/path", make_strip_prefix(from_root = "/path"))
    return unittest.end(env)

strip_prefix_test = unittest.make(_strip_prefix_test_impl)

def genpkg_analysis_tests():
    """Declare genpkg.bzl analysis tests"""
    _test_genpkg_contents()
    _test_genpkg_section()
    _test_genpkg_exclusions()
    _test_genpkg_extrepo()

    native.test_suite(
        name = "genpkg_analysis_tests",
        # We should find a way to get rid of this test list; it would be nice if
        # it could be derived from something else...
        tests = [
            # buildifier: don't sort
            # Simple tests
            ":pfg_no_strip_prefix",
            ":pfg_files_only",
            ":pfg_strip_testdata_from_pkg",
            ":pfg_strip_prefix_from_root",
            # Tests involving excluded files
            ":pfg_exclude_by_label_strip_all",
            ":pfg_exclude_by_filename_strip_all",
            ":pfg_exclude_by_label_strip_from_pkg",
            ":pfg_exclude_by_filename_strip_from_pkg",
            ":pfg_exclude_by_label_strip_from_root",
            ":pfg_exclude_by_filename_strip_from_root",
            # Tests involving external repositories
            ":pfg_extrepo_strip_all",
            ":pfg_extrepo_strip_from_pkg",
            ":pfg_extrepo_strip_from_root",
            ":pfg_extrepo_filegroup_strip_from_pkg",
            ":pfg_extrepo_filegroup_strip_from_root",
            ":pfg_pkgfilegroup_in_extrepo",
            # This one fits into the same category, but can't be aliased, apparently.
            #
            # The main purpose behind it is to verify cases wherein we build a
            # file, but then have it consumed by some remote package.
            "@test_external_repo//pkg:pfg_local_file_in_extrepo",
            # Tests involving the "section" attribute
            ":pfg_doc_section_test",
            ":pfg_bad_section_test",
        ],
    )

def genpkg_unit_tests():
    unittest.suite(
        "genpkg_unit_tests",
        strip_prefix_test,
    )
