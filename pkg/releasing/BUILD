load("@rules_python//python:defs.bzl", "py_binary", "py_library", "py_test")

package(
    default_visibility = ["//visibility:public"],
)

# WARNING: 2019-08-05. This is experimental and subject to change.
# It is expected to be available for use concurently with the Bazel
# 1.0 release.

# Sample usage:
# load("@rules_pkg//releasing:defs.bzl", "print_rel_notes")
# print_rel_notes(
#     name = "relnotes",
#     repo = "rules_pkg",
#     version = "2.1",
#     outs = ["relnotes.txt"],
# )

filegroup(
    name = "standard_package",
    srcs = glob([
        "BUILD",
        "*.bzl",
        "*.py",
    ]),
    visibility = ["@//distro:__pkg__"],
)

py_library(
    name = "release_utils",
    srcs = [
        "__init__.py",
        "release_tools.py",
    ],
    srcs_version = "PY3",
)

py_binary(
    name = "print_rel_notes",
    srcs = [
        "print_rel_notes.py",
    ],
    python_version = "PY3",
    deps = [
        ":release_utils",
    ],
)

py_test(
    name = "release_tools_test",
    srcs = ["release_tools_test.py"],
    deps = [
        ":release_utils",
    ],
)
