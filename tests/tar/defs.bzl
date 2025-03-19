"""Helpers for testing tar packaging."""

def _raw_symlinks_impl(ctx):
    link1 = ctx.actions.declare_symlink(ctx.label.name + "_link1")
    ctx.actions.symlink(output = link1, target_path = "../link1")

    link2 = ctx.actions.declare_symlink(ctx.label.name + "_link2")
    ctx.actions.symlink(output = link2, target_path = "../link2")

    return [DefaultInfo(
        files = depset([link1]),
        runfiles = ctx.runfiles([link2]),
    )]

raw_symlinks = rule(
    implementation = _raw_symlinks_impl,
)
