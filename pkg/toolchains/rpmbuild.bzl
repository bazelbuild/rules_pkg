# toolchain to provide the rpmbuild binary

RpmbuildInfo = provider(
    doc = """Platform inde artifact.""",
    fields = {
        "is_present": "Is rpmbuild actually available",
        "label": "The path to a target I will build",
        "path": "The path to a pre-built rpmbuild",
    },
)

def _rpmbuild_toolchain_impl(ctx):
    toolchain_info = platform_common.ToolchainInfo(
        rpmbuild = RpmbuildInfo(
            is_present = ctx.attr.path,
            label = ctx.attr.label,
            path = ctx.attr.path,
        ),
    )
    return [toolchain_info]

rpmbuild_toolchain = rule(
    implementation = _rpmbuild_toolchain_impl,
    attrs = {
        "label": attr.label(
            cfg = "exec",
            executable = True,
            allow_files = True,
        ),
        "path": attr.string(),
        "is_present": attr.bool(default=False),
    },
)


# Expose the is_present attribute of the resolve toolchain as a flag.
def _rpmbuild_toolchain_feature_impl(ctx):
    toolchain = ctx.toolchains["//toolchains:rpmbuild_toolchain_type"].rpmbuild
    print(dir(toolchain))
    value = "1" if toolchain.is_present else "0"
    return [config_common.FeatureFlagInfo(value = value)]

rpmbuild_toolchain_feature = rule(
    implementation = _rpmbuild_toolchain_feature_impl,
    attrs = {},
    toolchains = ["//toolchains:rpmbuild_toolchain_type"]
)


# Convenience function for use in workspaces.

def register_rpmbuild_toolchains():
    native.register_toolchains(
        "//toolchains:rpmbuild_linux_toolchain",
        "//toolchains:rpmbuild_missing_toolchain",
    )
