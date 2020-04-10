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

"""Tests for file mapping routines in pkg/experimental/pkg_filegroup.bzl"""

# NOTE: When making this module unexperimental, you can clean it up via calling something like this:
#
#   sed 's|experimental[_/]\?||' experimental/tests/pkg_filegroup_test.bzl

load("@bazel_skylib//lib:new_sets.bzl", "sets")
load("@bazel_skylib//lib:unittest.bzl", "analysistest", "asserts", "unittest")
load(
    "@rules_pkg//experimental:pkg_filegroup.bzl",
    "PackageDirInfo",
    "PackageFileInfo",
    "PackageSymlinkInfo",
    "make_strip_prefix",
    "pkg_filegroup",
    "pkg_mkdirs",
    "pkg_mklinks",
    "pkg_rename_single",
)

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
        # Other attributes can be tested here, but the most important one is the
        # destinations.
        "expected_dests": attr.string_list(
            mandatory = True,
        ),
        # attrs/section are always passed
        # through unchanged (and maybe
        # rejected)
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

def generic_bad_section_test(**kwargs):
    generic_neg_test(
        reason = "Invalid 'section' value",
        **kwargs
    )

def _test_pkg_filegroup_contents():
    # Test stripping when no arguments are provided (same as files_only=True)
    pkg_filegroup(
        name = "pfg_no_strip_prefix_g",
        srcs = ["testdata/hello.txt"],
        tags = ["manual"],
    )

    pkg_filegroup_contents_test(
        name = "pfg_no_strip_prefix",
        target_under_test = ":pfg_no_strip_prefix_g",
        expected_dests = ["hello.txt"],
    )

    # And now, files_only = True
    pkg_filegroup(
        name = "pfg_files_only_g",
        srcs = ["testdata/hello.txt"],
        strip_prefix = make_strip_prefix(files_only = True),
        tags = ["manual"],
    )

    pkg_filegroup_contents_test(
        name = "pfg_files_only",
        target_under_test = ":pfg_files_only_g",
        expected_dests = ["hello.txt"],
    )

    # Used in the following tests
    #
    # Note that since the pkg_filegroup rule is never actually used in anything
    # other than this test, nonexistent_script can be included with no ill effects. :P
    native.sh_binary(
        name = "test_script",
        srcs = ["testdata/nonexistent_script.sh"],
        tags = ["manual"],
    )

    # Test stripping from the package root
    pkg_filegroup(
        name = "pfg_from_pkg_g",
        srcs = [
            "testdata/hello.txt",
            ":test_script",
        ],
        strip_prefix = make_strip_prefix(from_pkg = "testdata/"),
        tags = ["manual"],
    )

    pkg_filegroup_contents_test(
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

    pkg_filegroup(
        name = "pfg_from_root_g",
        srcs = [":test_script"],
        strip_prefix = make_strip_prefix(from_root = "experimental/tests/"),
        tags = ["manual"],
    )

    pkg_filegroup_contents_test(
        name = "pfg_strip_prefix_from_root",
        target_under_test = ":pfg_from_root_g",
        expected_dests = [
            # The script itself
            "testdata/nonexistent_script.sh",
            # The generated target output, in this case, a symlink
            "test_script",
        ],
    )

def _test_pkg_filegroup_exclusions():
    # Normal filegroup, used in all of the below tests
    native.filegroup(
        name = "test_base_fg",
        srcs = [
            "testdata/config",
            "testdata/hello.txt",
        ],
    )

    # Tests to exclude from the case where stripping is done up to filenames
    pkg_filegroup(
        name = "pfg_exclude_by_label_strip_all_g",
        srcs = ["test_base_fg"],
        excludes = ["//experimental/tests:testdata/config"],
        tags = ["manual"],
    )
    pkg_filegroup_contents_test(
        name = "pfg_exclude_by_label_strip_all",
        target_under_test = ":pfg_exclude_by_label_strip_all_g",
        expected_dests = ["hello.txt"],
    )

    pkg_filegroup(
        name = "pfg_exclude_by_filename_strip_all_g",
        srcs = ["test_base_fg"],
        excludes = ["testdata/config"],
        tags = ["manual"],
    )
    pkg_filegroup_contents_test(
        name = "pfg_exclude_by_filename_strip_all",
        target_under_test = ":pfg_exclude_by_filename_strip_all_g",
        expected_dests = ["hello.txt"],
    )

    # Tests to exclude from the case where stripping is done from the package root
    pkg_filegroup(
        name = "pfg_exclude_by_label_strip_from_pkg_g",
        srcs = ["test_base_fg"],
        excludes = ["//experimental/tests:testdata/config"],
        strip_prefix = make_strip_prefix(from_pkg = "testdata"),
        tags = ["manual"],
    )
    pkg_filegroup_contents_test(
        name = "pfg_exclude_by_label_strip_from_pkg",
        target_under_test = ":pfg_exclude_by_label_strip_from_pkg_g",
        expected_dests = ["hello.txt"],
    )

    pkg_filegroup(
        name = "pfg_exclude_by_filename_strip_from_pkg_g",
        srcs = ["test_base_fg"],
        excludes = ["testdata/config"],
        strip_prefix = make_strip_prefix(from_pkg = "testdata"),
        tags = ["manual"],
    )
    pkg_filegroup_contents_test(
        name = "pfg_exclude_by_filename_strip_from_pkg",
        target_under_test = ":pfg_exclude_by_filename_strip_from_pkg_g",
        expected_dests = ["hello.txt"],
    )

    # Tests to exclude from the case where stripping is done from the root
    pkg_filegroup(
        name = "pfg_exclude_by_label_strip_from_root_g",
        srcs = ["test_base_fg"],
        excludes = ["//experimental/tests:testdata/config"],
        strip_prefix = make_strip_prefix(from_root = "experimental/tests"),
        tags = ["manual"],
    )
    pkg_filegroup_contents_test(
        name = "pfg_exclude_by_label_strip_from_root",
        target_under_test = ":pfg_exclude_by_label_strip_from_root_g",
        expected_dests = ["testdata/hello.txt"],
    )

    pkg_filegroup(
        name = "pfg_exclude_by_filename_strip_from_root_g",
        srcs = ["test_base_fg"],
        excludes = ["testdata/config"],
        strip_prefix = make_strip_prefix(from_root = "experimental/tests"),
        tags = ["manual"],
    )
    pkg_filegroup_contents_test(
        name = "pfg_exclude_by_filename_strip_from_root",
        target_under_test = ":pfg_exclude_by_filename_strip_from_root_g",
        expected_dests = ["testdata/hello.txt"],
    )

# Tests involving external repositories
def _test_pkg_filegroup_extrepo():
    # From external repo root, basenames only
    pkg_filegroup(
        name = "pfg_extrepo_strip_all_g",
        srcs = ["@experimental_test_external_repo//pkg:script"],
        tags = ["manual"],
    )
    pkg_filegroup_contents_test(
        name = "pfg_extrepo_strip_all",
        target_under_test = ":pfg_extrepo_strip_all_g",
        expected_dests = ["extproj.sh", "script"],
    )

    # From external repo root, relative to the "pkg" package
    pkg_filegroup(
        name = "pfg_extrepo_strip_from_pkg_g",
        srcs = ["@experimental_test_external_repo//pkg:script"],
        strip_prefix = make_strip_prefix(from_pkg = "dir"),
        tags = ["manual"],
    )
    pkg_filegroup_contents_test(
        name = "pfg_extrepo_strip_from_pkg",
        target_under_test = ":pfg_extrepo_strip_from_pkg_g",
        expected_dests = [
            "extproj.sh",  # "dir" is stripped
            "script",  # Nothing to strip
        ],
    )

    # From external repo root, relative to the "pkg" directory
    pkg_filegroup(
        name = "pfg_extrepo_strip_from_root_g",
        srcs = ["@experimental_test_external_repo//pkg:script"],
        strip_prefix = make_strip_prefix(from_root = "pkg"),
        tags = ["manual"],
    )
    pkg_filegroup_contents_test(
        name = "pfg_extrepo_strip_from_root",
        target_under_test = ":pfg_extrepo_strip_from_root_g",
        expected_dests = ["dir/extproj.sh", "script"],
    )

    native.filegroup(
        name = "extrepo_test_fg",
        srcs = ["@experimental_test_external_repo//pkg:dir/extproj.sh"],
    )

    # Test the case when a have a pkg_filegroup that targets a local filegroup
    # that has files in an external repo.
    pkg_filegroup(
        name = "pfg_extrepo_filegroup_strip_from_pkg_g",
        srcs = [":extrepo_test_fg"],
        # Files within filegroups should be considered relative to their
        # destination paths.
        strip_prefix = make_strip_prefix(from_pkg = ""),
    )
    pkg_filegroup_contents_test(
        name = "pfg_extrepo_filegroup_strip_from_pkg",
        target_under_test = ":pfg_extrepo_filegroup_strip_from_pkg_g",
        expected_dests = ["dir/extproj.sh"],
    )

    # Ditto, except strip from the workspace root instead
    pkg_filegroup(
        name = "pfg_extrepo_filegroup_strip_from_root_g",
        srcs = [":extrepo_test_fg"],
        # Files within filegroups should be considered relative to their
        # destination paths.
        strip_prefix = make_strip_prefix(from_root = "pkg"),
    )
    pkg_filegroup_contents_test(
        name = "pfg_extrepo_filegroup_strip_from_root",
        target_under_test = ":pfg_extrepo_filegroup_strip_from_root_g",
        expected_dests = ["dir/extproj.sh"],
    )

    # Reference a pkg_filegroup in @experimental_test_external_repo
    pkg_filegroup_contents_test(
        name = "pfg_pkg_filegroup_in_extrepo",
        target_under_test = "@experimental_test_external_repo//pkg:extproj_script_pfg",
        expected_dests = ["usr/bin/dir/extproj.sh"],
    )

def _test_pkg_filegroup_rename():
    # NOTE: unless rules contain "macro", they are not using the macro
    # "pfg_rename_single".  This is perhaps old (perhaps bad) naming convention.

    pkg_filegroup(
        name = "pfg_rename_single_g",
        srcs = [
            # Should come out relative to prefix and renames
            "testdata/hello.txt",
            # Should come out relative to prefix only
            "testdata/loremipsum.txt",
        ],
        prefix = "usr",
        renames = {
            "testdata/hello.txt": "share/goodbye.txt",
        },
        tags = ["manual"],
    )
    pkg_filegroup_contents_test(
        name = "pfg_rename_single",
        target_under_test = ":pfg_rename_single_g",
        expected_dests = [
            "usr/share/goodbye.txt",
            "usr/loremipsum.txt",
        ],
    )

    pkg_filegroup(
        name = "pfg_rename_multiple_g",
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
    pkg_filegroup_contents_test(
        name = "pfg_rename_multiple",
        target_under_test = ":pfg_rename_multiple_g",
        expected_dests = [
            "usr/share/goodbye.txt",
            "usr/doc/dolorsitamet.txt",
        ],
    )

    # Used in the following tests
    #
    # Note that since the pkg_filegroup rule is never actually used in anything
    # other than this test, nonexistent_script can be included with no ill
    # effects. :P
    native.sh_binary(
        name = "test_script_rename",
        srcs = ["testdata/nonexistent_script.sh"],
        tags = ["manual"],
    )

    # test_script_rename produces multiple outputs.  Thus, this test should
    # fail, as pkg_filegroup can't figure out what should actually be mapped to
    # the output destination.
    pkg_filegroup(
        name = "pfg_rename_rule_with_multiple_outputs_g",
        srcs = ["test_script_rename"],
        renames = {
            ":test_script_rename": "still_nonexistent_script",
        },
        tags = ["manual"],
    )
    generic_neg_test(
        name = "pfg_rename_rule_with_multiple_outputs",
        target_under_test = ":pfg_rename_rule_with_multiple_outputs_g",
    )

    # Fail because we tried to install a file that wasn't mentioned in the deps
    # list
    pkg_filegroup(
        name = "pfg_rename_single_missing_value_g",
        srcs = ["testdata/hello.txt"],
        prefix = "usr",
        renames = {
            "nonexistent_script": "nonexistent_output_location",
        },
        tags = ["manual"],
    )
    generic_neg_test(
        name = "pfg_rename_single_missing_value",
        target_under_test = ":pfg_rename_single_missing_value_g",
    )

    # Ditto, except for exclusions
    pkg_filegroup(
        name = "pfg_rename_single_excluded_value_g",
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
        name = "pfg_rename_single_excluded_value",
        target_under_test = ":pfg_rename_single_excluded_value_g",
    )

    # Test the macro
    pkg_rename_single(
        name = "pfg_rename_single_macro_g",
        src = "testdata/hello.txt",
        dest = "share/goodbye.txt",
        prefix = "usr",
        tags = ["manual"],
    )
    pkg_filegroup_contents_test(
        name = "pfg_rename_single_macro",
        target_under_test = ":pfg_rename_single_macro_g",
        expected_dests = ["usr/share/goodbye.txt"],
    )

def _test_pkg_filegroup_section():
    pkg_filegroup(
        name = "pfg_good_section",
        srcs = ["testdata/hello.txt"],
        section = "doc",
        tags = ["manual"],
    )

    pkg_filegroup_contents_test(
        name = "pfg_doc_section_test",
        target_under_test = ":pfg_good_section",
        expected_dests = ["hello.txt"],
    )

    pkg_filegroup(
        name = "pfg_bad_section",
        srcs = ["testdata/hello.txt"],
        section = "bad_section",
        tags = ["manual"],
    )

    generic_bad_section_test(
        name = "pfg_bad_section_test",
        target_under_test = ":pfg_bad_section",
    )

##########
# Test pkg_mkdirs
##########

def _pkg_mkdirs_contents_test_impl(ctx):
    env = analysistest.begin(ctx)
    target_under_test = analysistest.target_under_test(env)

    expected_dirs = sets.make(ctx.attr.expected_dirs)
    actual_dirs = sets.make(target_under_test[PackageDirInfo].dirs)

    asserts.new_set_equals(env, expected_dirs, actual_dirs, "pkg_mkdirs dirs do not match expectations")

    # Simple equality checks for the others
    asserts.equals(
        env,
        ctx.attr.expected_attrs,
        target_under_test[PackageDirInfo].attrs,
        "pkg_mkdir attrs do not match expectations",
    )
    asserts.equals(
        env,
        ctx.attr.expected_section,
        target_under_test[PackageDirInfo].section,
        "pkg_mkdir section does not match expectations",
    )

    return analysistest.end(env)

pkg_mkdirs_contents_test = analysistest.make(
    _pkg_mkdirs_contents_test_impl,
    attrs = {
        "expected_dirs": attr.string_list(
            mandatory = True,
        ),
        "expected_attrs": attr.string_list_dict(),
        "expected_section": attr.string(),
    },
)

def _test_pkg_mkdirs():
    # Reasonable base case
    pkg_mkdirs(
        name = "pfg_pkg_mkdirs_base_g",
        dirs = ["foo/bar", "baz"],
        attrs = {"unix": ["0711", "root", "sudo"]},
        tags = ["manual"],
    )
    pkg_mkdirs_contents_test(
        name = "pfg_pkg_mkdirs_base",
        target_under_test = "pfg_pkg_mkdirs_base_g",
        expected_dirs = ["foo/bar", "baz"],
        expected_attrs = {"unix": ["0711", "root", "sudo"]},
        expected_section = "dir",
    )

    # "docdir" is a valid attribute name
    pkg_mkdirs(
        name = "pfg_pkg_mkdirs_docdir_g",
        dirs = ["foo/bar", "baz"],
        attrs = {"unix": ["0555", "root", "sudo"]},
        section = "docdir",
        tags = ["manual"],
    )
    pkg_mkdirs_contents_test(
        name = "pfg_pkg_mkdirs_docdir",
        target_under_test = "pfg_pkg_mkdirs_docdir_g",
        expected_dirs = ["foo/bar", "baz"],
        expected_attrs = {"unix": ["0555", "root", "sudo"]},
        expected_section = "docdir",
    )

    pkg_mkdirs(
        name = "pfg_pkg_mkdirs_bad_attrs_g",
        dirs = ["foo/bar", "baz"],
        attrs = {"not_unix": ["derp"]},
        tags = ["manual"],
    )
    generic_neg_test(
        name = "pfg_pkg_mkdirs_bad_attrs",
        target_under_test = ":pfg_pkg_mkdirs_bad_attrs_g",
    )

    pkg_mkdirs(
        name = "pfg_pkg_mkdirs_bad_section_g",
        dirs = ["foo/bar", "baz"],
        section = "config",
        tags = ["manual"],
    )
    generic_neg_test(
        name = "pfg_pkg_mkdirs_bad_section",
        target_under_test = ":pfg_pkg_mkdirs_bad_section_g",
    )

##########
# Test pkg_mklinks
##########
def _pkg_mklinks_contents_test_impl(ctx):
    env = analysistest.begin(ctx)
    target_under_test = analysistest.target_under_test(env)

    asserts.equals(
        env,
        ctx.attr.expected_links,
        target_under_test[PackageSymlinkInfo].link_map,
        "pkg_mklinks link map does not match expectations",
    )

    # Simple equality checks for the others
    asserts.equals(
        env,
        ctx.attr.expected_attrs,
        target_under_test[PackageSymlinkInfo].attrs,
        "pkg_mklinks attrs do not match expectations",
    )
    asserts.equals(
        env,
        ctx.attr.expected_section,
        target_under_test[PackageSymlinkInfo].section,
        "pkg_mklinks section does not match expectations",
    )

    return analysistest.end(env)

pkg_mklinks_contents_test = analysistest.make(
    _pkg_mklinks_contents_test_impl,
    attrs = {
        "expected_links": attr.string_dict(
            mandatory = True,
        ),
        "expected_attrs": attr.string_list_dict(),
        "expected_section": attr.string(),
    },
)

def _test_pkg_mklinks():
    pkg_mklinks(
        name = "pfg_pkg_mklinks_base_g",
        links = {
            "bar": "foo",
            "qux": "baz",
        },
        tags = ["manual"],
    )

    pkg_mklinks_contents_test(
        name = "pfg_pkg_mklinks_base",
        target_under_test = ":pfg_pkg_mklinks_base_g",
        expected_links = {
            "bar": "foo",
            "qux": "baz",
        },
        expected_attrs = {"unix": ["0777", "-", "-"]},
    )

    pkg_mklinks(
        name = "pfg_pkg_mklinks_same_source_g",
        links = {
            "bar": "foo",
            "baz": "foo",
        },
        tags = ["manual"],
    )

    pkg_mklinks_contents_test(
        name = "pfg_pkg_mklinks_same_source",
        target_under_test = ":pfg_pkg_mklinks_same_source_g",
        expected_links = {
            "bar": "foo",
            "baz": "foo",
        },
        expected_attrs = {"unix": ["0777", "-", "-"]},
    )

    # Negative tests below
    pkg_mklinks(
        name = "pfg_pkg_mklinks_bad_attrs_g",
        links = {
            "bar": "foo",
            "qux": "baz",
        },
        attrs = {"the_dog_goes": ["bork"]},
        tags = ["manual"],
    )
    generic_neg_test(
        name = "pfg_pkg_mklinks_bad_attrs",
        target_under_test = ":pfg_pkg_mklinks_bad_attrs_g",
    )

##########
# Test make_strip_prefix()
##########

def _strip_prefix_test_impl(ctx):
    env = unittest.begin(ctx)
    asserts.equals(env, ".", make_strip_prefix(files_only = True))
    asserts.equals(env, "path", make_strip_prefix(from_pkg = "path"))
    asserts.equals(env, "path", make_strip_prefix(from_pkg = "/path"))
    asserts.equals(env, "/path", make_strip_prefix(from_root = "path"))
    asserts.equals(env, "/path", make_strip_prefix(from_root = "/path"))
    return unittest.end(env)

strip_prefix_test = unittest.make(_strip_prefix_test_impl)

def pkg_filegroup_analysis_tests():
    """Declare pkg_filegroup.bzl analysis tests"""
    _test_pkg_filegroup_contents()
    _test_pkg_filegroup_exclusions()
    _test_pkg_filegroup_extrepo()
    _test_pkg_filegroup_rename()
    _test_pkg_filegroup_section()
    _test_pkg_mkdirs()
    _test_pkg_mklinks()

    native.test_suite(
        name = "pkg_filegroup_analysis_tests",
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
            ":pfg_pkg_filegroup_in_extrepo",
            # This one fits into the same category, but can't be aliased, apparently.
            #
            # The main purpose behind it is to verify cases wherein we build a
            # file, but then have it consumed by some remote package.
            "@experimental_test_external_repo//pkg:pfg_local_file_in_extrepo",
            # Tests involving file renaming
            ":pfg_rename_single",
            ":pfg_rename_multiple",
            ":pfg_rename_rule_with_multiple_outputs",
            ":pfg_rename_single_missing_value",
            ":pfg_rename_single_excluded_value",
            ":pfg_rename_single_macro",
            # Tests involving the "section" attribute
            ":pfg_doc_section_test",
            ":pfg_bad_section_test",
            # Tests involving pkg_mkdirs
            ":pfg_pkg_mkdirs_base",
            ":pfg_pkg_mkdirs_docdir",
            ":pfg_pkg_mkdirs_bad_attrs",
            ":pfg_pkg_mkdirs_bad_section",
            # Tests involving pkg_mklinks
            ":pfg_pkg_mklinks_base",
            ":pfg_pkg_mklinks_same_source",
            ":pfg_pkg_mklinks_bad_attrs",
        ],
    )

def pkg_filegroup_unit_tests():
    unittest.suite(
        "pkg_filegroup_unit_tests",
        strip_prefix_test,
    )
