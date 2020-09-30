# -*- coding: utf-8 -*-

licenses(["notice"])

load("//:rpm.bzl", "pkg_rpm")
load("@rules_python//python:defs.bzl", "py_test")

py_test(
    name = "make_rpm_test",
    srcs = ["make_rpm_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    # rpmbuild is not available in windows
    tags = [
        "no_windows",
    ],
    deps = [
        "//:make_rpm_lib",
    ],
)

pkg_rpm(
    name = "test-rpm",
    data = ["//tests:archive_testdata"],
    debug = 1,
    release = "0",
    spec_file = "test_rpm.spec",
    version = "1",
)
