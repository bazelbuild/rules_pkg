
load("@rules_pkg//toolchains:rpmbuild.bzl", "rpmbuild_toolchain")

rpmbuild_toolchain(
    name = "prebuilt_rpmbuild",
    # You could also point to a target that builds rpmbuild from source.
    label = "//local:rpmbuild_binary"
)

toolchain(
    name = "local_rpmbuild",
    exec_compatible_with = [
        "@platforms//os:linux",
    ],
    target_compatible_with = [
        "@platforms//os:linux",
    ],
    toolchain = ":prebuilt_rpmbuild",
    toolchain_type = "@rules_pkg//toolchains:rpmbuild_toolchain_type",
)
