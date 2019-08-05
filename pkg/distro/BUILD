package(
    default_visibility = ["//visibility:private"],
)

load("@rules_pkg//:pkg.bzl", "pkg_tar")
load("@rules_pkg//:version.bzl", "version")
load("@rules_pkg//releasing:defs.bzl", "print_rel_notes")

# Build the artifact to put on the github release page.
pkg_tar(
    name = "rules_pkg-%s" % version,
    srcs = [
        "//:standard_package",
        "//releasing:standard_package",
    ],
    extension = "tar.gz",
    # It is all source code, so make it read-only.
    mode = "0444",
    # Make it owned by root so it does not have the uid of the CI robot.
    owner = "0.0",
    package_dir = ".",
    strip_prefix = ".",
)

print_rel_notes(
    name = "relnotes",
    outs = ["relnotes.txt"],
    repo = "rules_pkg",
    version = version,
)

py_test(
    name = "packaging_test",
    size = "large",
    srcs = [
        "packaging_test.py",
        ":release_version.py",
    ],
    data = [
        ":rules_pkg-%s.tar.gz" % version,
        "testdata/BUILD.tmpl",
    ],
    local = True,
    python_version = "PY3",
    tags = [
        "no_windows",
        "noci",
    ],
    deps = [
        "@bazel_tools//tools/python/runfiles",
        "@rules_pkg//releasing:release_utils",
    ],
)

genrule(
    name = "version_as_py",
    outs = ["release_version.py"],
    cmd = "echo RELEASE_VERSION = \\'%s\\' >$@" % version,
)
