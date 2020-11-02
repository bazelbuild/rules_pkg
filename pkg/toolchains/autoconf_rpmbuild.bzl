

def _write_build(rctx, path):
    if not path:
       path = ""
    rctx.file(
        "BUILD",
        content = """# This content is generated
load("@rules_pkg//toolchains:rpmbuild.bzl", "rpmbuild_toolchain")

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

    register_func = """# This content is generated

def register_rpmbuild_toolchain():
"""
    if not path:
       register_func += "    pass\n"
    else:
       register_func += """    native.register_toolchains("@%s//:rpmbuild_toolchain")\n""" % rctx.name
    rctx.file(
        "register_toolchain.bzl",
        content = register_func,
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

def register_autoconf(repo_name):
   native.register_toolchains("@%s//:rpmbuild_toolchain" % repo_name)
