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

load("my_package_name.bzl", "my_package_naming")
load("path_test.bzl", "path_tests")
load("//pkg:mappings.bzl", "pkg_attributes", "pkg_mkdirs", "pkg_mklink")
load("//pkg:pkg.bzl", "SUPPORTED_TAR_COMPRESSIONS", "pkg_tar", "pkg_zip")
load("//pkg:pkg_deb.bzl", "pkg_deb")
load("//tests/util:defs.bzl", "directory", "fake_artifact")
load("@rules_python//python:defs.bzl", "py_test")
load("@bazel_skylib//rules:copy_file.bzl", "copy_file")

licenses(["notice"])

exports_files(glob(["testdata/**"]))

filegroup(
    name = "archive_testdata",
    srcs = glob(["testdata/**"]) + [
        ":compressor",
        ":test_tar_compression",
        ":test_tar_package_dir",
        ":test_tar_package_dir_file",
    ],
    visibility = [
        "//pkg/legacy/tests:__subpackages__",
        "//tests:__subpackages__",
    ],
)

py_test(
    name = "archive_test",
    srcs = [
        "archive_test.py",
    ],
    data = [":archive_testdata"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//pkg/private:archive",
        "@bazel_tools//tools/python/runfiles",
    ],
)

py_test(
    name = "path_test",
    srcs = ["path_test.py"],
    data = ["//pkg:path.bzl"],
    python_version = "PY3",
    srcs_version = "PY3",
)

py_test(
    name = "helpers_test",
    srcs = ["helpers_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//pkg/private:helpers",
    ],
)

py_test(
    name = "make_rpm_test",
    srcs = ["make_rpm_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//pkg:make_rpm_lib",
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

pkg_mkdirs(
    name = "dirs",
    attributes = pkg_attributes(
        group = "bar",
        mode = "711",
        user = "foo",
    ),
    dirs = [
        "foodir",
    ],
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

copy_file(
    name = "zipcontent_loremipsum",
    src = "testdata/loremipsum.txt",
    out = "zipcontent/loremipsum.txt",
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
    deps = ["testdata/tar_test.tar"],
)

#
# Tests for package_file_name
#
my_package_naming(
    name = "my_package_variables",
    label = "some_value",
)

pkg_deb(
    name = "test_deb_naming",
    data = ":test_tar_naming",
    description = "desc",
    maintainer = "someone@somewhere.com",
    package = "some_name",
    package_file_name = "test_naming_{label}.deb",
    package_variables = ":my_package_variables",
    version = "1",
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

pkg_zip(
    name = "test_zip_naming",
    srcs = [
        ":BUILD",
    ],
    package_file_name = "test_naming_{label}.zip",
    package_variables = ":my_package_variables",
)

# This just proves that we would create the files via package_file_name rather
# than the default out file.
sh_test(
    name = "package_naming_aggregate_test",
    srcs = ["package_naming_aggregate_test.sh"],
    data = [
        ":test_deb_naming",
        ":test_tar_naming",
        ":test_zip_naming",
    ],
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
    package_dir_file = "testdata/test_tar_package_dir_file.txt",
)

pkg_tar(
    name = "test_tar_out",
    srcs = [
        ":BUILD",
    ],
    out = "out.tar",
)

pkg_zip(
    name = "test_zip_empty",
    srcs = [],
)

# The contents of this file should equal test_zip_empty
pkg_zip(
    name = "test_zip_empty_different_extension",
    srcs = [],
    extension = "otherkindofzip",
)

pkg_zip(
    name = "test_zip_basic",
    srcs = [
        "testdata/hello.txt",
        "testdata/loremipsum.txt",
        ":dirs",
    ],
)

pkg_zip(
    name = "test_zip_timestamp",
    srcs = [
        "testdata/hello.txt",
    ],
    timestamp = 1234567890,
)

pkg_zip(
    name = "test_zip_permissions",
    srcs = [
        "testdata/executable.sh",
    ],
    mode = "644",
    timestamp = 1234567890,
)

# This should be equal to test_zip_basic because timestamps are rounded
# up to Jan 1 1980.
pkg_zip(
    name = "test_zip_basic_timestamp_before_epoch",
    srcs = [
        "testdata/hello.txt",
        "testdata/loremipsum.txt",
        ":dirs",
    ],
    timestamp = 0,
)

pkg_zip(
    name = "test-zip-strip_prefix-empty",
    srcs = [
        "zipcontent_loremipsum",
    ],
    strip_prefix = "",
)

pkg_zip(
    name = "test-zip-strip_prefix-none",
    srcs = [
        "zipcontent_loremipsum",
    ],
)

pkg_zip(
    name = "test-zip-strip_prefix-zipcontent",
    srcs = [
        "zipcontent_loremipsum",
    ],
    strip_prefix = "zipcontent",
)

pkg_zip(
    name = "test-zip-strip_prefix-dot",
    srcs = [
        "zipcontent_loremipsum",
    ],
    strip_prefix = ".",
)

filegroup(
    name = "test_zip_strip_prefix",
    srcs = [
        "test-zip-strip_prefix-dot",
        "test-zip-strip_prefix-empty",
        "test-zip-strip_prefix-none",
        "test-zip-strip_prefix-zipcontent",
    ],
)

# All of these should produce the same zip file.
[pkg_zip(
    name = "test_zip_package_dir" + str(idx),
    srcs = [
        "testdata/hello.txt",
        "testdata/loremipsum.txt",
    ],
    package_dir = package_dir,
) for (idx, package_dir) in enumerate([
    "abc/def",
    "/abc/def",
    "/abc/def/",
])]

py_test(
    name = "zip_test",
    srcs = [
        "zip_test.py",
    ],
    data = [
        "test_zip_empty.zip",
        "test_zip_basic.zip",
        "test_zip_package_dir0.zip",
        "test_zip_timestamp.zip",
        "test_zip_permissions.zip",
        "test-zip-strip_prefix-empty.zip",
        "test-zip-strip_prefix-none.zip",
        "test-zip-strip_prefix-zipcontent.zip",
        "test-zip-strip_prefix-dot.zip",

        # these could be replaced with diff_test() rules (from skylib)
        "test_zip_basic_timestamp_before_epoch.zip",
        "test_zip_empty_different_extension.otherkindofzip",
        "test_zip_package_dir1.zip",
        "test_zip_package_dir2.zip",
    ],
    python_version = "PY3",
    deps = [
        "//pkg/private:build_zip",
        "@bazel_tools//tools/python/runfiles",
    ],
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
    build_tar = "//pkg/private:build_tar",
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
        "testdata/file_with_a_ridiculously_long_name_consectetur_adipiscing_elit_fusce_laoreet_lorem_neque_sed_pharetra_erat.txt",
    ],
    strip_prefix = "testdata",
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
    ],
    package_dir = "a_tree",
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
        ":test_tar_package_dir_substitution.tar",
        ":test-tar-long-filename",
        ":test-tar-repackaging-long-filename.tar",
        ":test-tar-tree-artifact",
        ":test-tar-with-runfiles",
    ] + [
        ":test-tar-basic-%s" % compression
        for compression in SUPPORTED_TAR_COMPRESSIONS
    ] + [
        ":test-tar-inclusion-%s" % compression
        for compression in SUPPORTED_TAR_COMPRESSIONS
    ],
    python_version = "PY3",
    deps = [
        "//pkg/private:archive",
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

# Used within experimental/tests/ for external repo genpkg tests
filegroup(
    name = "loremipsum_txt",
    srcs = [
        "testdata/loremipsum.txt",
    ],
    visibility = ["//visibility:public"],
)

pkg_tar(
    name = "test-tar-compression-from-extension-targz",
    srcs = [
        "testdata/loremipsum.txt",
    ],
    extension = ".tar.gz",
)

pkg_tar(
    name = "test-tar-compression-from-extension-tgz",
    srcs = [
        "testdata/loremipsum.txt",
    ],
    extension = "tgz",
)

pkg_tar(
    name = "test-tar-compression-from-extension-bz2",
    srcs = [
        "testdata/loremipsum.txt",
    ],
    extension = ".bz2",
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

pkg_tar(
    name = "stamped_tar",
    srcs = ["BUILD"],
    stamp = 1,
)

pkg_zip(
    name = "stamped_zip",
    srcs = ["BUILD"],
    stamp = 1,
)

# Note that this only tests that stamping works. Other tests cover the case
# of archive members having the default, epoch, time stamp.
py_test(
    name = "stamp_test",
    srcs = [
        "stamp_test.py",
    ],
    data = [
        "stamped_tar.tar",
        "stamped_zip.zip",
    ],
    python_version = "PY3",
    deps = [
        "@bazel_tools//tools/python/runfiles",
    ],
)

path_tests(name = "path_tests")
