# toolchain to provide the rpmbuild binary

RpmbuildInfo = provider(
    doc = """Platform inde artifact.""",
    fields = {
        "label": "The path to a target I will build",
        "path": "The path to a pre-built rpmbuild",
    },
)

def _rpmbuild_toolchain_impl(ctx):
    toolchain_info = platform_common.ToolchainInfo(
        rpmbuild = RpmbuildInfo(
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
    },
)

def register_rpmbuild_toolchains():
    native.register_toolchains(
        "//toolchains:rpmbuild_linux_toolchain",
        "//toolchains:rpmbuild_missing_toolchain",
    )
