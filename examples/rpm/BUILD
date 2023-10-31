load("@rules_pkg//pkg:mappings.bzl", "pkg_filegroup")
load("@rules_pkg//pkg:rpm.bzl", "pkg_rpm")

pkg_filegroup(
    name = "rpm_filegroup",
    srcs = [
        "//rpm/main:exe",
    ],
    prefix = "/usr/bin",
)

pkg_rpm(
    name = "rpm",
    package_name = "example",
    license = "example",
    summary = "example",
    version = "1.0.0",
    release = "1",
    description = "example",
    srcs = [
        ":rpm_filegroup",
    ],
)
