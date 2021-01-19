def print_rel_notes(
        name,
        repo,
        version,
        outs = None,
        setup_file = "",
        deps_method = "",
        toolchains_method = "",
        org = "bazelbuild",
        mirror_host = None):
    tarball_name = ":%s-%s.tar.gz" % (repo, version)
    cmd = [
        "$(location //releasing:print_rel_notes)",
        "--org=%s" % org,
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
    if mirror_host:
        cmd.append("--mirror_host=%s" % mirror_host)
    cmd.append(">$@")
    native.genrule(
        name = "relnotes",
        srcs = [
            tarball_name,
        ],
        outs = outs or ["relnotes.txt"],
        cmd = " ".join(cmd),
        tools = [
            "//releasing:print_rel_notes",
        ],
    )
