# -*- coding: utf-8 -*-
load("@rules_python//python:defs.bzl", "py_binary", "py_library")

licenses(["notice"])

exports_files(
    glob(["*.bzl"]),
    visibility = ["//visibility:public"],
)

filegroup(
    name = "standard_package",
    srcs = glob([
        "*.bzl",
        "*.py",
        "*.md",
    ]) + [
        "BUILD",
        "LICENSE",
        "//experimental:standard_package",
    ],
    visibility = ["//distro:__pkg__"],
)

exports_files(
    ["WORKSPACE"],
    visibility = ["//distro:__pkg__"],
)


# Exposes the value of the --stamp blaze flag so that codegen modules
# which can use volatile build info know whether to depend on it.
config_setting(
    name = "is_stamped_build",
    values = {"stamp": "1"},
)

py_library(
    name = "archive",
    srcs = [
        "__init__.py",
        "archive.py",
    ],
    srcs_version = "PY3",
    visibility = [
        "//experimental:__pkg__",
        "//tests:__pkg__",
    ],
)

py_library(
    name = "helpers",
    srcs = [
        "__init__.py",
        "helpers.py",
    ],
    srcs_version = "PY3",
    visibility = [
        "//experimental:__pkg__",
        "//tests:__pkg__",
    ],
)

py_binary(
    name = "build_tar",
    srcs = ["build_tar.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    visibility = ["//visibility:public"],
    deps = [
        ":archive",
        ":helpers",
    ],
)

py_binary(
    name = "build_zip",
    srcs = ["build_zip.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    visibility = ["//visibility:public"],
    deps = [
        ":archive",
        ":helpers",
    ],
)

py_binary(
    name = "make_deb",
    srcs = ["make_deb.py"],
    python_version = "PY3",
    visibility = ["//visibility:public"],
    deps = [
        ":helpers",
    ],
)

# Used by pkg_rpm in rpm.bzl.
py_binary(
    name = "make_rpm",
    srcs = ["make_rpm.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    visibility = ["//visibility:public"],
    deps = [
        ":archive",
        ":make_rpm_lib",
    ],
)

py_library(
    name = "make_rpm_lib",
    srcs = ["make_rpm.py"],
    srcs_version = "PY3",
    visibility = [
        "//experimental:__pkg__",
        "//tests:__pkg__",
    ],
    deps = [
        ":archive",
        ":helpers",
    ],
)
