load("@rules_python//python:defs.bzl", "py_library")

licenses(["notice"])

config_setting(
    name = "stamp",
    values = {"stamp": "1"},
    visibility = ["//visibility:private"],
)

genrule(
    name = "volatile_status",
    srcs = [],
    outs = ["volatile_status.txt"],
    cmd = "cp bazel-out/volatile-status.txt $@",
    stamp = True,
    # This should be private to rules in :pkg.bzl, but that is not possible.
    visibility = ["//visibility:public"],
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
