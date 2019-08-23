

def _my_rule_impl(ctx):
    """Implementation of my_rule."""

    content = [f.path + '\n' for f in ctx.files.deps]
    ctx.actions.write(ctx.outputs.out, ''.join(content))
    return OutputGroupInfo(out=[ctx.outputs.out]);


my_rule = rule(
    implementation = _my_rule_impl,
    doc = "A simple rule which lists its deps in its output.",
    attrs = {
        "deps": attr.label_list(
            allow_files = True,
            doc = "A list of rules that are dependencies of this rule.",
        ),
        "out": attr.output(
            mandatory = True,
            doc = "Output file containing some function of the deps",
        ),
    }
)
