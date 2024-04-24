# Package an executable up for distribution
#
load("@rules_pkg//pkg:mappings.bzl", "pkg_files", "pkg_attributes")
load("@rules_python//python:defs.bzl", "py_binary")

cc_binary(
    name = "hello_world",
    srcs = ["hello_world.cc"],
)

py_binary(
    name = "hello_world_py",
    main = "hello_world.py",
    srcs = ["hello_world.py"],
)

pkg_files(
    name = "exe",
    srcs = [
        ":hello_world",
        ":hello_world_py",
    ],
    visibility = ["//visibility:public"],
    attributes = pkg_attributes(
        mode = "0755",
        user = "root",
        group = "root",
    ),
)
