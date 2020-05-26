# -*- coding: utf-8 -*-
licenses(["notice"])  # Apache 2.0

load("@//:pkg.bzl", "pkg_deb", "pkg_tar", "pkg_zip")
load("@//:rpm.bzl", "pkg_rpm")
load("@rules_python//python:defs.bzl", "py_test")

genrule(
    name = "generate_files",
    outs = [
        "etc/nsswitch.conf",
        "usr/titi",
    ],
    cmd = "for i in $(OUTS); do echo 1 >$$i; done",
)

pkg_tar(
    name = "test_tar_package_dir",
    srcs = [
        ":etc/nsswitch.conf",
    ],
    package_dir = "/package"
)

pkg_tar(
    name = "test_tar_package_dir_file",
    srcs = [
        ":etc/nsswitch.conf",
    ],
    package_dir_file = "testdata/test_tar_package_dir_file.txt"
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

        # these could be replaced with diff_test() rules (from skylib)
        "test_zip_basic_timestamp_before_epoch.zip",
        "test_zip_empty_different_extension.otherkindofzip",
        "test_zip_package_dir1.zip",
        "test_zip_package_dir2.zip",
    ],
    deps = [
        "@//:build_zip",
        "@bazel_tools//tools/python/runfiles",
    ],
)

filegroup(
    name = "archive_testdata",
    srcs = glob(["testdata/**"]) + [
        ":test_tar_package_dir",
        ":test_tar_package_dir_file"
    ],
    visibility = ["//visibility:private"],
)

py_test(
    name = "archive_test",
    srcs = [
        "archive_test.py",
    ],
    data = [":archive_testdata"],
    python_version = "PY3",
    srcs_version = "PY2AND3",
    tags = [
        # TODO(laszlocsomor): fix on Windows or describe why it cannot pass.
        "no_windows",
    ],
    deps = [
        "@//:archive",
        "@bazel_tools//tools/python/runfiles",
    ],
)

py_test(
    name = "path_test",
    srcs = ["path_test.py"],
    data = ["@//:path.bzl"],
    srcs_version = "PY2AND3",
)

py_test(
    name = "make_rpm_test",
    srcs = ["make_rpm_test.py"],
    python_version = "PY3",
    srcs_version = "PY2AND3",
    # rpmbuild is not available in windows
    tags = [
        "no_windows",
    ],
    deps = [
        "@//:make_rpm_lib",
        "@//:archive",
    ],
)

py_test(
    name = "helpers_test",
    srcs = ["helpers_test.py"],
    python_version = "PY3",
    srcs_version = "PY2AND3",
    deps = [
        "@//:archive",
    ],
)

genrule(
    name = "test-deb-preinst",
    outs = ["test-deb.preinst"],
    cmd = "echo -n \"#!/usr/bin/env bash\n# tete ®, Й, ק ,م, ๗, あ, 叶, 葉, 말, ü and é\necho fnord\" > \"$@\"",
)

pkg_deb(
    name = "test-deb",
    built_using = "some_test_data (0.1.2)",
    conffiles = [
        "/etc/nsswitch.conf",
        "/etc/other",
    ],
    config = ":testdata/config",
    data = ":test-tar-gz.tar.gz",
    depends = [
        "dep1",
        "dep2",
    ],
    description = "toto ®, Й, ק ,م, ๗, あ, 叶, 葉, 말, ü and é",
    distribution = "trusty",
    maintainer = "soméone@somewhere.com",
    make_deb = "@//:make_deb",
    package = "titi",
    breaks = ["oldbrokenpkg"],
    replaces = ["oldpkg"],
    templates = ":testdata/templates",
    preinst = ":test-deb-preinst",
    urgency = "low",
    version = "test",
)

pkg_rpm(
    name = "test-rpm",
    version = "1",
    release = "0",
    data = [":archive_testdata"],
    spec_file = "test_rpm.spec",
    debug = 1,
)

pkg_deb(
    name = "test-deb-py2",
    built_using = "some_test_data (0.1.2)",
    conffiles = [
        "/etc/nsswitch.conf",
        "/etc/other",
    ],
    config = ":testdata/config",
    data = ":test-tar-gz.tar.gz",
    depends = [
        "dep1",
        "dep2",
    ],
    description = "toto ®, Й, ק ,م, ๗, あ, 叶, 葉, 말, ü and é",
    distribution = "trusty",
    maintainer = "soméone@somewhere.com",
    make_deb = "@//:make_deb_py2",
    package = "titi",
    breaks = ["oldbrokenpkg"],
    replaces = ["oldpkg"],
    templates = ":testdata/templates",
    preinst = ":test-deb-preinst",
    urgency = "low",
    version = "test_py2",
)

[pkg_tar(
    name = "test-tar-%s" % ext[1:],
    srcs = [
        ":etc/nsswitch.conf",
        ":usr/titi",
    ],
    build_tar = "@//:build_tar",
    extension = "tar%s" % ext,
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
    build_tar = "@//:build_tar",
    deps = [":test-tar-%s" % ext],
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

sh_test(
    name = "build_test_deb",
    size = "medium",
    srcs = [
        "build_test_deb.sh",
    ],
    data = [
        "testenv.sh",
        ":test-deb.deb",
        ":test-deb-py2.deb",
        ":titi_test_all.changes",
    ],
    tags = [
        # dpkg tools are only available on debian
        "no_macos",
        "no_windows",
    ],
    deps = [
        "@rules_pkg//third_party/test/shell:bashunit",
    ],
)

sh_test(
    name = "build_test_tar",
    size = "medium",
    srcs = [
        "build_test_tar.sh",
    ],
    data = [
        "testenv.sh",
        ":archive_testdata",
        ":test-tar-.tar",
        ":test-tar-bz2.tar.bz2",
        ":test-tar-empty_dirs.tar",
        ":test-tar-empty_files.tar",
        ":test-tar-files_dict.tar",
        ":test-tar-gz.tar.gz",
        ":test-tar-inclusion-.tar",
        ":test-tar-inclusion-bz2.tar",
        ":test-tar-inclusion-gz.tar",
        ":test-tar-inclusion-xz.tar",
        ":test-tar-mtime.tar",
        ":test-tar-strip_prefix-dot.tar",
        ":test-tar-strip_prefix-empty.tar",
        ":test-tar-strip_prefix-etc.tar",
        ":test-tar-strip_prefix-none.tar",
        ":test-tar-xz.tar.xz",
        ":titi_test_all.changes",
    ],
    tags = [
        # archive.py requires xzcat, which is not available by default on Mac
        "no_macos",
        # TODO(laszlocsomor): fix on Windows or describe why it cannot pass.
        "no_windows",
    ],
    deps = [
        "@//third_party/test/shell:bashunit",
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
