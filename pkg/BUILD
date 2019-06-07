# -*- coding: utf-8 -*-
licenses(["notice"])  # Apache 2.0

exports_files(
    glob(["*.bzl"]),
    visibility = ["//visibility:public"],
)

py_library(
    name = "archive",
    srcs = [
        "__init__.py",
        "archive.py",
    ],
    srcs_version = "PY2AND3",
    visibility = ["@//tests:__pkg__"],
)

py_binary(
    name = "build_tar",
    srcs = ["build_tar.py"],
    python_version = "PY2",
    srcs_version = "PY2AND3",
    visibility = ["//visibility:public"],
    deps = [
        ":archive",
        "@abseil_py//absl/flags",
    ],
)

py_binary(
    name = "make_deb",
    srcs = ["make_deb.py"],
    python_version = "PY2",
    srcs_version = "PY2AND3",
    visibility = ["//visibility:public"],
    deps = [
        ":archive",
        "@abseil_py//absl/flags",
    ],
)

# Used by pkg_rpm in rpm.bzl.
py_binary(
    name = "make_rpm",
    srcs = ["make_rpm.py"],
    python_version = "PY2",
    srcs_version = "PY2AND3",
    visibility = ["//visibility:public"],
    deps = [
        ":make_rpm_lib",
    ],
)

py_library(
    name = "make_rpm_lib",
    srcs = ["make_rpm.py"],
    srcs_version = "PY2AND3",
    visibility = ["//visibility:public"],
    deps = [
        "@abseil_py//absl/flags",
    ],
)
