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
# -*- coding: utf-8 -*-
"""Tests for pkg_tar."""

# buildifier: disable=bzl-visibility
load("//pkg:mappings.bzl", "pkg_files", "strip_prefix")
load("//pkg/private/tar:tar.bzl", "SUPPORTED_TAR_COMPRESSIONS", "pkg_tar")
load("//tests:my_package_name.bzl", "my_package_naming")
load("//tests/util:defs.bzl", "directory", "fake_artifact")
load("@rules_python//python:defs.bzl", "py_test")
load("@bazel_skylib//rules:copy_file.bzl", "copy_file")

package(default_applicable_licenses = ["//:license"])

py_test(
    name = "tar_writer_test",
    srcs = [
        "tar_writer_test.py",
    ],
    data = [
        ":compressor",
        ":test_tar_compression",
        ":test_tar_package_dir",
        ":test_tar_package_dir_file",
        "//tests:testdata/tar_test.tar",
        "//tests:testdata/tar_test.tar.bz2",
        "//tests:testdata/tar_test.tar.gz",
        "//tests:testdata/tar_test.tar.xz",
        "//tests:testdata/test_tar_package_dir_file.txt",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//pkg/private/tar:tar_writer",
        "@bazel_tools//tools/python/runfiles",
    ],
)

genrule(
    name = "generate_files",
    outs = [
        "etc/nsswitch.conf",
        "usr/titi",
    ],
    cmd = "for i in $(OUTS); do echo 1 >$$i; done",
)

directory(
    name = "generate_tree",
    contents = "hello there",
    filenames = [
        # buildifier: don't sort
        "b/e",
        "a/a",
        "b/c/d",
        "b/d",
        "a/b/c",
    ],
)

py_binary(
    name = "compressor",
    srcs = ["compressor.py"],
    python_version = "PY3",
    srcs_version = "PY3",
)

pkg_tar(
    name = "test_tar_compression",
    compressor = ":compressor",
    compressor_args = "-a -b -c",
    deps = ["//tests:testdata/tar_test.tar"],
)

#
# Tests for package_file_name
#
my_package_naming(
    name = "my_package_variables",
    label = "some_value",
)

pkg_tar(
    name = "test_tar_naming",
    srcs = [
        ":BUILD",
    ],
    package_file_name = "test_naming_{label}.tar",
    package_variables = ":my_package_variables",
)

pkg_tar(
    name = "test_tar_package_dir_substitution",
    srcs = [
        ":BUILD",
    ],
    package_dir = "level1/{label}/level3",
    package_variables = ":my_package_variables",
)

pkg_tar(
    name = "test_tar_package_dir",
    srcs = [
        ":etc/nsswitch.conf",
    ],
    package_dir = "/package",
)

pkg_tar(
    name = "test_tar_package_dir_file",
    srcs = [
        ":etc/nsswitch.conf",
    ],
    package_dir_file = "//tests:testdata/test_tar_package_dir_file.txt",
)

pkg_tar(
    name = "test_tar_out",
    srcs = [
        ":BUILD",
    ],
    out = "out.tar",
)

[pkg_tar(
    name = "test-tar-basic-%s" % ext,
    srcs = [
        ":etc/nsswitch.conf",
        ":usr/titi",
    ],
    extension = "tar.%s" % ext if ext else "tar",
    mode = "0644",
    modes = {"usr/titi": "0755"},
    owner = "42.24",
    ownername = "titi.tata",
    ownernames = {"etc/nsswitch.conf": "tata.titi"},
    owners = {"etc/nsswitch.conf": "24.42"},
    package_dir = "/",
    strip_prefix = ".",
    symlinks = {"usr/bin/java": "/path/to/bin/java"},
) for ext in SUPPORTED_TAR_COMPRESSIONS]

[pkg_tar(
    name = "test-tar-inclusion-%s" % ext,
    build_tar = "//pkg/private/tar:build_tar",
    deps = [
        ":test-tar-basic-%s" % ext,
        ":test_tar_naming",
    ],
) for ext in SUPPORTED_TAR_COMPRESSIONS]

pkg_tar(
    name = "test-tar-strip_prefix-empty",
    srcs = [
        ":etc/nsswitch.conf",
    ],
    strip_prefix = "",
)

pkg_tar(
    name = "test-tar-strip_prefix-none",
    srcs = [
        ":etc/nsswitch.conf",
    ],
)

pkg_tar(
    name = "test-tar-strip_prefix-etc",
    srcs = [
        ":etc/nsswitch.conf",
    ],
    strip_prefix = "etc",
)

pkg_tar(
    name = "test-tar-strip_prefix-dot",
    srcs = [
        ":etc/nsswitch.conf",
        "@bazel_tools//tools/python/runfiles",
    ],
    strip_prefix = ".",
)

pkg_tar(
    name = "test-tar-strip_prefix-substring",
    srcs = [
        ":etc/nsswitch.conf",
    ],
    strip_prefix = "et",
)

pkg_tar(
    name = "test-tar-files_dict",
    files = {
        ":etc/nsswitch.conf": "not-etc/mapped-filename.conf",
    },
)

pkg_tar(
    name = "test-tar-empty_files",
    empty_files = [
        "/a",
        "/b",
    ],
    mode = "0o777",
)

pkg_tar(
    name = "test-tar-empty_dirs",
    empty_dirs = [
        "/tmp",
        "/pmt",
    ],
    mode = "0o777",
)

pkg_tar(
    name = "test-tar-mtime",
    srcs = [
        ":etc/nsswitch.conf",
    ],
    mtime = 946684740,  # 1999-12-31, 23:59
    portable_mtime = False,
)

pkg_tar(
    name = "test-tar-long-filename",
    srcs = [
        "//tests:testdata/file_with_a_ridiculously_long_name_consectetur_adipiscing_elit_fusce_laoreet_lorem_neque_sed_pharetra_erat.txt",
    ],
    # TODO(https://github.com/bazelbuild/rules_pkg/issues/462): The old test
    # used to have strip_prefix. But strip_prefix is just plain broken w.r.t.
    # files from other packages. We end up with an internal expected data_path
    # of tests/tar/<strip_prefix>. But the files coming in have the real paths.
    # strip_prefix = "testdata",
)

pkg_tar(
    name = "test-tar-repackaging-long-filename",
    package_dir = "can_i_repackage_a_file_with_a_long_name",
    deps = [
        ":test-tar-long-filename",
    ],
)

pkg_tar(
    name = "test-tar-tree-artifact",
    srcs = [
        ":generate_tree",
        "//tests:loremipsum_txt",
    ],
    package_dir = "a_tree",
)

pkg_files(
    name = "tree_noroot",
    srcs = [
        ":generate_tree",
    ],
    strip_prefix = "generate_tree",
)

pkg_tar(
    name = "test-tar-tree-artifact-noroot",
    srcs = [
        ":tree_noroot",
        "//tests:loremipsum_txt",
    ],
    package_dir = "a_tree",
)

fake_artifact(
    name = "a_program",
    files = ["//tests:testdata/executable.sh"],
    runfiles = ["BUILD"],
)

pkg_tar(
    name = "test-tar-with-runfiles",
    srcs = [
        ":a_program",
    ],
    include_runfiles = True,
)

pkg_tar(
    name = "test_tar_leading_dotslash",
    srcs = [
        "//tests:loremipsum_txt",
    ],
    package_dir = ".",
)

py_test(
    name = "pkg_tar_test",
    size = "medium",
    srcs = [
        "pkg_tar_test.py",
    ],
    data = [
        ":test-tar-empty_dirs.tar",
        ":test-tar-empty_files.tar",
        ":test-tar-files_dict.tar",
        ":test-tar-mtime.tar",
        ":test-tar-strip_prefix-dot.tar",
        ":test-tar-strip_prefix-empty.tar",
        ":test-tar-strip_prefix-etc.tar",
        ":test-tar-strip_prefix-none.tar",
        ":test-tar-strip_prefix-substring.tar",
        ":test_tar_leading_dotslash",
        ":test_tar_package_dir_substitution.tar",
        ":test-tar-long-filename",
        ":test-tar-repackaging-long-filename.tar",
        ":test-tar-tree-artifact",
        ":test-tar-tree-artifact-noroot",
        ":test-tar-with-runfiles",
        "//tests:testdata/tar_test.tar",
        "//tests:testdata/tar_test.tar.bz2",
        "//tests:testdata/tar_test.tar.gz",
        "//tests:testdata/tar_test.tar.xz",
        "//tests:testdata/test_tar_package_dir_file.txt",
    ] + [
        ":test-tar-basic-%s" % compression
        for compression in SUPPORTED_TAR_COMPRESSIONS
    ] + [
        ":test-tar-inclusion-%s" % compression
        for compression in SUPPORTED_TAR_COMPRESSIONS
    ],
    python_version = "PY3",
    deps = [
        "//pkg/private/tar:tar_writer",
        "@bazel_tools//tools/python/runfiles",
    ],
)

test_suite(
    name = "windows_tests",
    tags = [
        "-slow",
    ],
    visibility = ["//visibility:private"],
)

test_suite(
    name = "all_windows_tests",
    tests = [":windows_tests"],
)

pkg_tar(
    name = "test-tar-compression-from-extension-targz",
    srcs = [
        "//tests:testdata/loremipsum.txt",
    ],
    extension = ".tar.gz",
)

pkg_tar(
    name = "test-tar-compression-from-extension-tgz",
    srcs = [
        "//tests:testdata/loremipsum.txt",
    ],
    extension = "tgz",
)

pkg_tar(
    name = "test-tar-compression-from-extension-bz2",
    srcs = [
        "//tests:testdata/loremipsum.txt",
    ],
    extension = ".bz2",
)

py_test(
    name = "is_compressed_test",
    srcs = ["is_compressed_test.py"],
    data = [
        ":test-tar-compression-from-extension-bz2",
        ":test-tar-compression-from-extension-targz",
        ":test-tar-compression-from-extension-tgz",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "@bazel_tools//tools/python/runfiles",
    ],
)
