

def _write_build(rctx, path):
    if not path:
       path = ""
    rctx.file(
        'BUILD',
        content = """# This content is generated
load("@rules_pkg//toolchains:rpmbuild.bzl", "rpmbuild_toolchain")

constraint_setting(name = "rpmbuild_present")

constraint_value(
    name = "no",
    constraint_setting = "rpmbuild_present",
)

constraint_value(
    name = "yes",
    constraint_setting = "rpmbuild_present",
)

rpmbuild_toolchain(
    name = "rpmbuild",
    path = "%s",
)

toolchain(
    name = "rpmbuild_toolchain",
    toolchain = ":rpmbuild",
    toolchain_type = "@rules_pkg//toolchains:rpmbuild_toolchain_type",
)
""" % path,
        executable=False)

def _autoconf_rpmbuild_impl(rctx):
    if not rctx.attr.installed_rpmbuild_path:
       rpmbuild_path = rctx.which("rpmbuild")
    else:
       rpmbuild_path = rctx.attr.installed_rpmbuild_path
    _write_build(rctx=rctx, path=rpmbuild_path)
    # I would like to register the toolchain here, but you can only call
    # register_toolchains from the WORKSPACE file.
    print(dir(rctx))

autoconf_rpmbuild = repository_rule(
    implementation=_autoconf_rpmbuild_impl,
    local=True,
    attrs={
        "installed_rpmbuild_path": attr.string(default=""),
    }
)
