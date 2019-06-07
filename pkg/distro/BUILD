package(
    default_visibility = ["//visibility:private"],
)

load("@rules_pkg//:pkg.bzl", "pkg_tar")

VERSION = "0.1.0"

pkg_tar(
    name = "rules_pkg-%s" % VERSION,
    srcs = [
        "@rules_pkg//:standard_package",
    ],
    extension = "tar.gz",
    mode = "0644",
    owner = "0.0",
    package_dir = ".",
)

py_library(
    name = "util",
    srcs = [
        "__init__.py",
        "release_tools.py",
        "release_version.py",
    ],
    srcs_version = "PY3",
    deps = [
        "@bazel_tools//tools/python/runfiles",
    ],
)

py_binary(
    name = "print_rel_notes",
    srcs = [
        "print_rel_notes.py",
    ],
    data = [
        ":rules_pkg-%s.tar.gz" % VERSION,
    ],
    python_version = "PY3",
    deps = [
        ":util",
        "@bazel_tools//tools/python/runfiles",
    ],
)

py_test(
    name = "packaging_test",
    size = "large",
    srcs = [
        "packaging_test.py",
    ],
    data = [
        ":rules_pkg-%s.tar.gz" % VERSION,
        "testdata/BUILD.tmpl",
    ],
    local = True,
    python_version = "PY3",
    tags = [
        "no_windows",
        "noci",
    ],
    deps = [
        ":util",
        "@bazel_tools//tools/python/runfiles",
    ],
)
