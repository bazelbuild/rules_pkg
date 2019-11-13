

def print_rel_notes(name, repo, version, outs=None, setup_file="",
                    deps_method="", toolchains_method=""):
    tarball_name = ":%s-%s.tar.gz" % (repo, version)
    cmd = [
        "$(location @rules_pkg//releasing:print_rel_notes)",
        "--repo=%s" % repo,
        "--version=%s" % version,
        "--tarball=$(location %s)" % tarball_name,
    ]
    if setup_file:
      cmd.append("--setup_file=%s" % setup_file)
    if deps_method:
      cmd.append("--deps_method=%s" % deps_method)
    if toolchains_method:
      cmd.append("--toolchains_method=%s" % toolchains_method)
    cmd.append(">$@")
    native.genrule(
        name = "relnotes",
        srcs = [
            tarball_name,
        ],
        outs = outs or ["relnotes.txt"],
        cmd = " ".join(cmd),
        tools = [
            "@rules_pkg//releasing:print_rel_notes",
        ],
    )
