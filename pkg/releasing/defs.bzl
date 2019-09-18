

def print_rel_notes(name, repo, version, outs=None, has_deps_file=True):
    tarball_name = ":%s-%s.tar.gz" % (repo, version)
    native.genrule(
        name = "relnotes",
        srcs = [
            tarball_name,
        ],
        outs = outs or ["relnotes.txt"],
        cmd = " ".join([
            "$(location @rules_pkg//releasing:print_rel_notes)",
            repo,
            version,
            "$(location %s)" % tarball_name,
            str(has_deps_file),
            ">$@",
        ]),
        tools = [
            "@rules_pkg//releasing:print_rel_notes",
        ],
    )
