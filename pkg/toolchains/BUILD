# toolchain to provide the rpmbuild binary

load("//toolchains:rpmbuild.bzl", "rpmbuild_toolchain")

filegroup(
    name = "standard_package",
    srcs = glob([
        "*",
    ]),
    visibility = ["//distro:__pkg__"],
)

constraint_setting(name = "is_rpmbuild_present")

constraint_value(
    name = "rpmbuild_present",
    constraint_setting = "is_rpmbuild_present",
)

toolchain_type(
    name = "rpmbuild_toolchain_type",
    visibility = ["//visibility:public"],
)

rpmbuild_toolchain(
    name = "system_rpmbuild",
    path = "/usr/bin/rpmbuild",
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
