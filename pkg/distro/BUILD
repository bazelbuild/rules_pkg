load("//:pkg.bzl", "pkg_tar")
load("//:version.bzl", "version")
load("//releasing:defs.bzl", "print_rel_notes")
load("@bazel_skylib//:bzl_library.bzl", "bzl_library")
load("@bazel_stardoc//stardoc:stardoc.bzl", "stardoc")
load("@rules_python//python:defs.bzl", "py_test")

licenses(["notice"])

package(
    default_visibility = ["//visibility:private"],
)

# Build the artifact to put on the github release page.
pkg_tar(
    name = "rules_pkg-%s" % version,
    srcs = [
        ":small_workspace",
        "//:standard_package",
        "//toolchains:standard_package",
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

genrule(
    name = "small_workspace",
    srcs = ["//:WORKSPACE"],
    outs = ["WORKSPACE"],
    cmd = "sed -e '/### INTERNAL ONLY/,$$d' $(location //:WORKSPACE) >$@",
)

print_rel_notes(
    name = "relnotes",
    outs = ["relnotes.txt"],
    deps_method = "rules_pkg_dependencies",
    org = 'bazelbuild',
    repo = "rules_pkg",
    version = version,
    mirror_host = 'mirror.bazel.build'
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
        "//releasing:release_utils",
    ],
)

genrule(
    name = "version_as_py",
    outs = ["release_version.py"],
    cmd = "echo RELEASE_VERSION = \\'%s\\' >$@" % version,
)

bzl_library(
    name = "rules_pkg_lib",
    srcs = [
        "//:package_variables.bzl",
        "//:path.bzl",
        "//:pkg.bzl",
        "//:providers.bzl",
        "//:rpm.bzl",
        "//:version.bzl",
    ],
    visibility = ["//visibility:private"],
)

stardoc(
    name = "docs_deb",
    out = "pkg_deb.md",
    input = "//:pkg.bzl",
    symbol_names = [
        "pkg_deb",
        "pkg_deb_impl",
    ],
    deps = [":rules_pkg_lib"],
)

stardoc(
    name = "docs_tar",
    out = "pkg_tar.md",
    input = "//:pkg.bzl",
    symbol_names = [
        "pkg_tar",
        "pkg_tar_impl",
    ],
    deps = [":rules_pkg_lib"],
)

stardoc(
    name = "docs_zip",
    out = "pkg_zip.md",
    input = "//:pkg.bzl",
    symbol_names = [
        "pkg_zip",
        "pkg_zip_impl",
    ],
    deps = [":rules_pkg_lib"],
)

stardoc(
    name = "docs_rpm",
    out = "pkg_rpm.md",
    input = "//:rpm.bzl",
    deps = [":rules_pkg_lib"],
)
