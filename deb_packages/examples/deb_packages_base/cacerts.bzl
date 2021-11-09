"""A rule to unpack ca certificates from the debian package."""

def _impl(ctx):
    args = "%s %s %s" % (ctx.executable._extract.path, ctx.file.deb.path, ctx.outputs.out.path)
    ctx.actions.run_shell(
        command = args,
        inputs = [ctx.executable._extract, ctx.file.deb],
        outputs = [ctx.outputs.out],
    )

cacerts = rule(
    attrs = {
        "deb": attr.label(
            allow_single_file = [".deb"],
            mandatory = True,
        ),
        # Implicit dependencies.
        "_extract": attr.label(
            default = Label("//examples/deb_packages/deb_packages_base:extract_certs"),
            cfg = "host",
            executable = True,
            allow_files = True,
        ),
    },
    executable = False,
    outputs = {
        "out": "%{name}.tar",
    },
    implementation = _impl,
)
