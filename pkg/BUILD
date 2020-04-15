# -*- coding: utf-8 -*-
load("@rules_python//python:defs.bzl", "py_binary", "py_library")

licenses(["notice"])  # Apache 2.0

exports_files(
    glob(["*.bzl"]),
    visibility = ["//visibility:public"],
)

filegroup(
    name = "standard_package",
    srcs = glob(["BUILD", "*.bzl", "*.py", "*.md"]),
    visibility = ["@//distro:__pkg__"],
)

py_library(
    name = "archive",
    srcs = [
        "__init__.py",
        "archive.py",
        "helpers.py"
    ],
    srcs_version = "PY2AND3",
    # This points to a fundemental bazel workspace deficiency. What we need is a
    # way to specify "the workspace that this BUILD or .bzl file comes from".
    # I do not want to say '@rules_pkg'. That forces my name on everyone who uses
    # me. '@' seems to be the outer workspace.
    visibility = [
        "@//experimental:__pkg__",
        "@rules_pkg//experimental:__pkg__",
        "@//tests:__pkg__",
        "@rules_pkg//tests:__pkg__"
    ],
)

py_binary(
    name = "build_tar",
    srcs = ["build_tar.py"],
    python_version = "PY2",
    srcs_version = "PY2AND3",
    visibility = ["//visibility:public"],
    deps = [
        ":archive",
    ],
)

py_binary(
    name = "build_zip",
    srcs = ["build_zip.py"],
    visibility = ["//visibility:public"],
    deps = [":archive"],
)

py_binary(
    name = "make_deb",
    srcs = ["make_deb.py"],
    python_version = "PY3",
    visibility = ["//visibility:public"],
    deps = [
        ":archive",
    ],
)

py_binary(
    name = "make_deb_py2",
    srcs = ["make_deb.py"],
    main = "make_deb.py",
    python_version = "PY2",
    srcs_version = "PY2AND3",
    visibility = ["//visibility:public"],
    deps = [
        ":archive",
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
        ":archive",
        ":make_rpm_lib",
    ],
)

py_library(
    name = "make_rpm_lib",
    srcs = ["make_rpm.py"],
    srcs_version = "PY2AND3",
    visibility = ["//visibility:public"],
)
