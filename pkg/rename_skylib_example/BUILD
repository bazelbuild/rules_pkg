load("@my_bazel_skylib//:bzl_library.bzl", "bzl_library")
load("@my_bazel_skylib//lib:paths.bzl", "paths")
load("@io_bazel_skydoc//stardoc:stardoc.bzl", "stardoc")

# load(":my_rule.bzl", "my_rule")

bzl_library(
    name = "my_rule",
    srcs = [
        "my_rule.bzl",
    ],
    visibility = ["//visibility:public"],
)

stardoc(
    name = "my_rule_doc",
    out = "my_rule_doc.md",
    input = ":my_rule.bzl",
    symbol_names = [
        "my_rule",
    ],
    deps = [":my_rule"],
)

cc_library(
    name = paths.basename("foo/bar/dummy"),
    srcs = ["lib.cc"],
)
