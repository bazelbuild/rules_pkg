# toolchain to provide the rpmbuild binary

load("//toolchains:rpmbuild.bzl", "rpmbuild_toolchain", "rpmbuild_toolchain_feature")

filegroup(
    name = "standard_package",
    srcs = glob([
        "*",
    ]),
    visibility = ["//distro:__pkg__"],
)

# Expose the is_present attribute of the resolved toolchain as a feature flag.
rpmbuild_toolchain_feature(
    name = "is_rpmbuild_present",
    visibility = ["//visibility:public"],
)

toolchain_type(
    name = "rpmbuild_toolchain_type",
    visibility = ["//visibility:public"],
)

rpmbuild_toolchain(
    name = "system_rpmbuild",
    path = "/usr/bin/rpmbuild",
    is_present = True,
)

toolchain(
    name = "rpmbuild_linux_toolchain",
    exec_compatible_with = [
        "@platforms//os:linux",
    ],
    target_compatible_with = [
        "@platforms//os:linux",
    ],
    toolchain = ":system_rpmbuild",
    toolchain_type = ":rpmbuild_toolchain_type",
)

# The fallback toolchain
rpmbuild_toolchain(
    name = "no_rpmbuild",
    path = "",
)

toolchain(
    name = "rpmbuild_missing_toolchain",
    toolchain = ":no_rpmbuild",
    toolchain_type = ":rpmbuild_toolchain_type",
)
