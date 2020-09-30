# -*- coding: utf-8 -*-

licenses(["notice"])

load("//:rpm.bzl", "pkg_rpm")

pkg_rpm(
    name = "test-rpm",
    data = ["//tests:archive_testdata"],
    debug = 1,
    release = "0",
    spec_file = "test_rpm.spec",
    version = "1",
)
