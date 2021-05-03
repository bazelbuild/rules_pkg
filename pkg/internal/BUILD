"""rules_pkg internal code.

This is subject to change at any time.
"""

load("@rules_python//python:defs.bzl", "py_library")

licenses(["notice"])

config_setting(
    name = "stamp",
    values = {"stamp": "1"},
    visibility = ["//visibility:private"],
)

py_library(
    name = "build_info",
    srcs = [
        "build_info.py",
    ],
    srcs_version = "PY3",
    visibility = [
        "//:__pkg__",
        "//tests:__pkg__",
    ],
)
