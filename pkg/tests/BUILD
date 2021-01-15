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

licenses(["notice"])

load("//:pkg.bzl", "pkg_deb", "pkg_tar", "pkg_zip")
load("@rules_python//python:defs.bzl", "py_test")
load("@bazel_skylib//rules:copy_file.bzl", "copy_file")

load(":my_package_name.bzl", "my_package_naming")

exports_files(glob(["testdata/**"]))

filegroup(
    name = "archive_testdata",
    srcs = glob(["testdata/**"]) + [
        ":test_tar_package_dir",
        ":test_tar_package_dir_file",
    ],
    visibility = ["//tests:__subpackages__"],
)

py_test(
    name = "archive_test",
    srcs = [
        "archive_test.py",
    ],
    data = [":archive_testdata"],
    python_version = "PY3",
    srcs_version = "PY3",
    tags = [
        # TODO(laszlocsomor): fix on Windows or describe why it cannot pass.
        "no_windows",
    ],
    deps = [
        "//:archive",
        "@bazel_tools//tools/python/runfiles",
    ],
)


py_test(
    name = "path_test",
    srcs = ["path_test.py"],
    data = ["//:path.bzl"],
    python_version = "PY3",
    srcs_version = "PY3",
)

py_test(
    name = "helpers_test",
    srcs = ["helpers_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//:helpers",
    ],
)

py_test(
    name = "make_rpm_test",
    srcs = ["make_rpm_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//:make_rpm_lib",
    ],
)

# Exposes the value of the compilation mode to the package naming.
config_setting(
    name = "special_build",
    values = {"define": "SPECIAL=1"},
)

my_package_naming(
    name = "my_package_variables",
    label = "-alpha",
    # There is no important reason to use a config_setting and a select. This
    # is really just to show a technique.
    # TBD: Move this into a cookbook of examples.
    special_build = select({
        ":special_build": "-IsSpecial",
        "//conditions:default": "",
    }),
)

genrule(
    name = "generate_files",
    outs = [
        "etc/nsswitch.conf",
        "usr/titi",
    ],
    cmd = "for i in $(OUTS); do echo 1 >$$i; done",
)

copy_file(
    name = "zipcontent_loremipsum",
    src = "testdata/loremipsum.txt",
    out = "zipcontent/loremipsum.txt",
)

# Try building with various flag combinations to show the abilities
#   bazel build :test_tar_naming -c dbg --define=SPECIAL=1
pkg_tar(
    name = "test_tar_naming",
    srcs = [
        ":BUILD",
    ],
    package_file_name = "test_naming-{target_cpu}-{compilation_mode}{label}{special_build}.tar",
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
        "test-zip-strip_prefix-empty",
        "test-zip-strip_prefix-none",
        "test-zip-strip_prefix-zipcontent",
        "test-zip-strip_prefix-dot",
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
        "//:build_zip",
        "@bazel_tools//tools/python/runfiles",
    ],
)

pkg_deb(
    name = "test-deb",
    breaks = ["oldbrokenpkg"],
    built_using = "some_test_data (0.1.2)",
    conffiles = [
        "/etc/nsswitch.conf",
        "/etc/other",
    ],
    config = ":testdata/config",
    data = ":test-tar-basic-gz.tar.gz",
    depends = [
        "dep1",
        "dep2",
    ],
    description = "toto ®, Й, ק ,م, ๗, あ, 叶, 葉, 말, ü and é",
    distribution = "trusty",
    maintainer = "soméone@somewhere.com",
    make_deb = "//:make_deb",
    package = "titi",
    preinst = "testdata/deb_preinst",
    replaces = ["oldpkg"],
    provides = ["hello"],
    templates = ":testdata/templates",
    urgency = "low",
    version = "test",
)

[pkg_tar(
    name = "test-tar-basic-%s" % ext[1:],
    srcs = [
        ":etc/nsswitch.conf",
        ":usr/titi",
    ],
    extension = "tar%s" % ext,
    # extension = ext[1:],
    mode = "0644",
    modes = {"usr/titi": "0755"},
    owner = "42.24",
    ownername = "titi.tata",
    ownernames = {"etc/nsswitch.conf": "tata.titi"},
    owners = {"etc/nsswitch.conf": "24.42"},
    package_dir = "/",
    strip_prefix = ".",
    symlinks = {"usr/bin/java": "/path/to/bin/java"},
) for ext in [
    "",
    ".gz",
    ".bz2",
    ".xz",  # This will breaks if xzcat is not installed
]]

[pkg_tar(
    name = "test-tar-inclusion-%s" % ext,
    build_tar = "//:build_tar",
    deps = [
        ":test-tar-basic-%s" % ext,
        ":test_tar_naming",
    ],
) for ext in [
    "",
    "gz",
    "bz2",
    "xz",
]]

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

py_test(
    name = "pkg_tar_test",
    size = "medium",
    srcs = [
        "pkg_tar_test.py",
    ],
    data = [
        ":test-tar-basic-.tar",
        ":test-tar-basic-bz2.tar.bz2",
        ":test-tar-basic-gz.tar.gz",
        ":test-tar-basic-xz.tar.xz",
        ":test-tar-empty_dirs.tar",
        ":test-tar-empty_files.tar",
        ":test-tar-files_dict.tar",
        ":test-tar-inclusion-.tar",
        ":test-tar-inclusion-bz2.tar",
        ":test-tar-inclusion-gz.tar",
        ":test-tar-inclusion-xz.tar",
        ":test-tar-mtime.tar",
        ":test-tar-strip_prefix-dot.tar",
        ":test-tar-strip_prefix-empty.tar",
        ":test-tar-strip_prefix-etc.tar",
        ":test-tar-strip_prefix-none.tar",
        ":test-tar-strip_prefix-substring.tar",
    ],
    python_version = "PY3",
    deps = [
        "@bazel_tools//tools/python/runfiles",
    ],
)

py_test(
    name = "pkg_deb_test",
    size = "medium",
    srcs = [
        "pkg_deb_test.py",
    ],
    python_version = "PY3",
    data = [
        ":titi_test_all.deb",
        ":titi_test_all.changes",
    ],
    deps = [
        "//:archive",
        "@bazel_tools//tools/python/runfiles",
    ],
)

test_suite(
    name = "windows_tests",
    tags = [
        "-no_windows",
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
