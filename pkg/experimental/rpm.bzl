# Copyright 2019-2020 The Bazel Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# NOTE: This is different from make_rpm.py in pkg/, and is specific to the
# `pkg_rpm` rule in this directory.

"""Provides rules for creating RPM packages via pkg_filegroup and friends."""

load("@rules_pkg//experimental:pkg_filegroup.bzl", "PackageDirInfo", "PackageFileInfo")

rpm_filetype = [".rpm"]

spec_filetype = [".spec", ".spec.in"]

def _pkg_rpm_impl(ctx):
    """Implements the pkg_rpm rule."""

    files = []
    args = ["--name=" + ctx.label.name]

    if ctx.attr.debug:
        args.append("--debug")

    if ctx.attr.rpmbuild_path:
        args.append("--rpmbuild=" + ctx.attr.rpmbuild_path)

    #### rpm spec "preamble"
    preamble_pieces = []

    # rpm_name takes precedence over name if provided
    if ctx.attr.rpm_name:
        rpm_name = ctx.attr.rpm_name
    else:
        rpm_name = ctx.attr.name
    preamble_pieces.append("Name: " + rpm_name)

    # Version can be specified by a file or inlined.
    if ctx.attr.version_file:
        if ctx.attr.version:
            fail("Both version and version_file attributes were specified")

        preamble_pieces.append("Version: ${VERSION_FROM_FILE}")
        args.append("--version=@" + ctx.file.version_file.path)
        files.append(ctx.file.version_file)
    elif ctx.attr.version:
        preamble_pieces.append("Version: " + ctx.attr.version)
    else:
        fail("None of the version or version_file attributes were specified")

    # Release can be specified by a file or inlined.
    if ctx.attr.release_file:
        if ctx.attr.release:
            fail("Both release and release_file attributes were specified")

        preamble_pieces.append("Release: ${RELEASE_FROM_FILE}")
        args.append("--release=@" + ctx.file.release_file.path)
        files.append(ctx.file.release_file)
    elif ctx.attr.release:
        preamble_pieces.append("Release: " + ctx.attr.release)
    else:
        fail("None of the release or release_file attributes were specified")

    if ctx.attr.summary:
        preamble_pieces.append("Summary: " + ctx.attr.summary)
    if ctx.attr.url:
        preamble_pieces.append("URL: " + ctx.attr.url)
    if ctx.attr.license:
        preamble_pieces.append("License: " + ctx.attr.license)
    if ctx.attr.group:
        preamble_pieces.append("Group: " + ctx.attr.group)

    # TODO: BuildArch is usually not hardcoded in spec files, unless the package
    # is indeed restricted to a particular CPU architecture, or is actually
    # "noarch".  This will become more of a concern when we start providing
    # source RPMs.
    #
    # In the meantime, this will allow the "architecture" attribute to take
    # effect.
    if ctx.attr.architecture:
        preamble_pieces.append("BuildArch: " + ctx.attr.architecture)

    preamble_file = ctx.actions.declare_file(
        "{}.spec.preamble".format(rpm_name),
    )
    ctx.actions.write(
        output = preamble_file,
        content = "\n".join(preamble_pieces),
    )
    files.append(preamble_file)
    args.append("--preamble=" + preamble_file.path)

    #### %description

    if ctx.attr.description_file:
        if ctx.attr.description:
            fail("Both description and description_file attributes were specified")
        description_file = ctx.file.description_file
    elif ctx.attr.description:
        description_file = ctx.actions.declare_file(
            "{}.spec.description".format(rpm_name),
        )
        ctx.actions.write(
            output = description_file,
            content = ctx.attr.description,
        )
    else:
        fail("None of the description or description_file attributes were specified")

    files.append(description_file)
    args.append("--description=" + description_file.path)

    #### Non-procedurally-generated scriptlets

    substitutions = {}
    if ctx.attr.pre_scriptlet_file:
        if ctx.attr.pre_scriptlet:
            fail("Both pre_scriptlet and pre_scriptlet_file attributes were specified")
        pre_scriptlet_file = ctx.file.pre_scriptlet_file
        files.append(pre_scriptlet_file)
        args.append("--pre_scriptlet=" + pre_scriptlet_file.path)
    elif ctx.attr.pre_scriptlet:
        scriptlet_file = ctx.actions.declare_file(ctx.label.name + ".pre_scriptlet")
        files.append(scriptlet_file)
        ctx.actions.write(scriptlet_file,  ctx.attr.pre_scriptlet)
        args.append("--pre_scriptlet=" + scriptlet_file.path)

    if ctx.attr.post_scriptlet_file:
        if ctx.attr.post_scriptlet:
            fail("Both post_scriptlet and post_scriptlet_file attributes were specified")
        post_scriptlet_file = ctx.file.post_scriptlet_file
        files.append(post_scriptlet_file)
        args.append("--post_scriptlet=" + post_scriptlet_file.path)
    elif ctx.attr.post_scriptlet:
        scriptlet_file = ctx.actions.declare_file(ctx.label.name + ".post_scriptlet")
        files.append(scriptlet_file)
        ctx.actions.write(scriptlet_file,  ctx.attr.post_scriptlet)
        args.append("--post_scriptlet=" + scriptlet_file.path)

    if ctx.attr.preun_scriptlet_file:
        if ctx.attr.preun_scriptlet:
            fail("Both preun_scriptlet and preun_scriptlet_file attributes were specified")
        preun_scriptlet_file = ctx.file.preun_scriptlet_file
        files.append(preun_scriptlet_file)
        args.append("--preun_scriptlet=" + preun_scriptlet_file.path)
    elif ctx.attr.preun_scriptlet:
        scriptlet_file = ctx.actions.declare_file(ctx.label.name + ".preun_scriptlet")
        files.append(scriptlet_file)
        ctx.actions.write(scriptlet_file,  ctx.attr.preun_scriptlet)
        args.append("--preun_scriptlet=" + scriptlet_file.path)

    if ctx.attr.postun_scriptlet_file:
        if ctx.attr.postun_scriptlet:
            fail("Both postun_scriptlet and postun_scriptlet_file attributes were specified")
        postun_scriptlet_file = ctx.file.postun_scriptlet_file
        files.append(postun_scriptlet_file)
        args.append("--postun_scriptlet=" + postun_scriptlet_file.path)
    elif ctx.attr.postun_scriptlet:
        scriptlet_file = ctx.actions.declare_file(ctx.label.name + ".postun_scriptlet")
        files.append(scriptlet_file)
        ctx.actions.write(scriptlet_file,  ctx.attr.postun_scriptlet)
        args.append("--postun_scriptlet=" + scriptlet_file.path)

    #### Expand the spec file template; prepare data files

    spec_file = ctx.actions.declare_file("%s.spec" % rpm_name)
    ctx.actions.expand_template(
        template = ctx.file.spec_template,
        output = spec_file,
        substitutions = substitutions,
    )
    args.append("--spec_file=" + spec_file.path)
    files.append(spec_file)

    args.append("--out_file=" + ctx.outputs.rpm.path)

    # Add data files.
    if ctx.file.changelog:
        files.append(ctx.file.changelog)
        args.append(ctx.file.changelog.path)

    files += ctx.files.data

    #### Sanity checking

    # Ensure that no destinations collide.  RPMs that fail this check may be
    # sane, but the output may also create hard-to-debug issues.  Better to err
    # on the side of correctness here.
    dest_check_map = {}
    for d in ctx.attr.data:
        # d is a Target

        # FIXME: if/when we start to consider other providers here, we may want
        # to create a subroutine to consolidate these loops.

        # NOTE: This does not detect cases where directories are not named
        # consistently.  For example, all of these may collide in reality, but
        # won't be detected by the below:
        #
        # 1) usr/lib/libfoo.a
        # 2) /usr/lib/libfoo.a
        # 3) %{_libdir}/libfoo.a
        #
        # The rule of thumb, regardless of how these checks below are done, is
        # to be consistent with path naming conventions.
        #
        # There is also an unsolved question of determining how to handle
        # subdirectories of "PackageFileInfo" targets that are actually
        # directories.
        if PackageFileInfo in d:
            pfi = d[PackageFileInfo]
            for dest in pfi.dests:
                if dest in dest_check_map:
                    fail(
                        "Destination '{0}' is provided by both {1} and {2}; please ensure each destination is provided by exactly one incoming rule".format(
                            dest,
                            dest_check_map[dest],
                            d.label,
                        ),
                        "data",
                    )
                else:
                    dest_check_map[dest] = d.label

        if PackageDirInfo in d:
            pdi = d[PackageDirInfo]
            for dest in pdi.dirs:
                if dest in dest_check_map:
                    fail(
                        "Destination '{0}' is provided by both {1} and {2}; please ensure each destination is provided by exactly one incoming rule".format(
                            dest,
                            dest_check_map[dest],
                            d.label,
                        ),
                        "data",
                    )
                else:
                    dest_check_map[dest] = d.label

    #### Procedurally-generated scripts/lists (%install, %files)

    # Build up the install script
    install_script_pieces = []
    if ctx.attr.debug:
        install_script_pieces.append("set -x")

    # {0} is the source, {1} is the dest
    install_file_stanza_fmt = """
install -d %{{buildroot}}/$(dirname {1})
cp -r {0} %{{buildroot}}/{1}
    """

    # {0} is the directory name
    #
    # This may not be strictly necessary, given that they'll be created in the
    # CPIO when rpmbuild processes the `%files` list.
    install_dir_stanza_fmt = """
install -d %{{buildroot}}/{0}
    """

    # Build up the RPM files list (%files -f)
    rpm_files_list = []

    # Iterate over all incoming data, creating datasets as we go from the
    # actual contents of the RPM.
    #
    # This is a naive approach to script creation is almost guaranteed to
    # produce an installation script that is longer than necessary.  A better
    # implementation would track directories that are created and ensure that
    # they aren't unnecessarily recreated.
    for elem in ctx.attr.data:
        if PackageFileInfo in elem:
            pfi = elem[PackageFileInfo]
            file_base = "%attr({}) {}".format(
                ", ".join(pfi.attrs["unix"]),
                "%" + pfi.section if pfi.section else "",
            )
            for (source, dest) in zip(pfi.srcs, pfi.dests):
                rpm_files_list.append(file_base + " /" + dest)

                install_script_pieces.append(install_file_stanza_fmt.format(
                    source.path,
                    dest,
                ))
        if PackageDirInfo in elem:
            pdi = elem[PackageDirInfo]
            file_base = "%attr({}) {}".format(
                ", ".join(pdi.attrs["unix"]),
                "%" + pdi.section if pdi.section else "",
            )
            for d in pdi.dirs:
                rpm_files_list.append(file_base + " /" + d)

                install_script_pieces.append(install_dir_stanza_fmt.format(
                    d,
                ))

    install_script = ctx.actions.declare_file("{}.spec.install".format(rpm_name))
    ctx.actions.write(
        install_script,
        "\n".join(install_script_pieces),
    )
    files.append(install_script)
    args.append("--install_script=" + install_script.path)

    rpm_files_file = ctx.actions.declare_file(
        "{}.spec.files".format(rpm_name),
    )
    ctx.actions.write(
        rpm_files_file,
        "\n".join(rpm_files_list),
    )
    files.append(rpm_files_file)
    args.append("--file_list=" + rpm_files_file.path)

    for f in ctx.files.data:
        args.append(f.path)

    #### Call the generator script.

    ctx.actions.run(
        mnemonic = "MakeRpm",
        executable = ctx.executable._make_rpm,
        use_default_shell_env = True,
        arguments = args,
        inputs = files,
        outputs = [ctx.outputs.rpm],
        env = {
            "LANG": "en_US.UTF-8",
            "LC_CTYPE": "UTF-8",
            "PYTHONIOENCODING": "UTF-8",
            "PYTHONUTF8": "1",
        },
    )

    #### Output construction

    # Link the RPM to the expected output name.
    ctx.actions.run(
        executable = "ln",
        arguments = [
            "-s",
            ctx.outputs.rpm.basename,
            ctx.outputs.out.path,
        ],
        inputs = [ctx.outputs.rpm],
        outputs = [ctx.outputs.out],
    )

    # Link the RPM to the RPM-recommended output name.
    if "rpm_nvra" in dir(ctx.outputs):
        ctx.actions.run(
            executable = "ln",
            arguments = [
                "-s",
                ctx.outputs.rpm.basename,
                ctx.outputs.rpm_nvra.path,
            ],
            inputs = [ctx.outputs.rpm],
            outputs = [ctx.outputs.rpm_nvra],
        )

# TODO(nacl): this relies on deprecated behavior (should use Providers
# instead), it should be removed at some point.
def _pkg_rpm_outputs(name, rpm_name, version, release):
    actual_rpm_name = rpm_name or name
    outputs = {
        "out": actual_rpm_name + ".rpm",
        "rpm": actual_rpm_name + "-%{architecture}.rpm",
    }

    # The "rpm_nvra" output follows the recommended package naming convention of
    # Name-Version-Release.Arch.rpm
    # See http://ftp.rpm.org/max-rpm/ch-rpm-file-format.html
    if version and release:
        outputs["rpm_nvra"] = actual_rpm_name + "-%{version}-%{release}.%{architecture}.rpm"

    return outputs

# Define the rule.
pkg_rpm = rule(
    doc = """Creates an RPM format package via `pkg_filegroup` and friends.

    The uses the outputs of the rules in `pkg_filegroup.bzl` to construct arbitrary RPM
    packages.  Attributes of this rule provide preamble information and
    scriptlets, which are then used to compose a valid RPM spec file.

    The meat is in the `data` attribute, which is handled like so:

    - `pkg_filegroup`s provide mappings of targets to output files:

      - They are copied to their destination after their destination directory
        is created.

      - No directory ownership is implied; they will typically be owned by
        `root.root` and given permissions associated with `root`'s `umask`,
        typically 0755, unless otherwise overidden.

      - File permissions are set in the `%files` manifest.  `%config` or other
        `%files` properties are propagated from the `section` attribute.

    - `pkg_mkdirs` provide directories and directory ownership. They are
      created in the package tree directly.  They are owned as specified by the
      `section` attribute, which typically is the same as `%dir`.

    This rule will fail at analysis time if:

    - Any `data` input may create the same destination, regardless of other
      attributes.

    Currently, two outputs are guaranteed to be produced: "%{name}.rpm", and
    "%{name}-%{architecture}.rpm". If the "version" and "release" arguments are
    non-empty, a third output will be produced, following the RPM-recommended
    N-V-R.A format (Name-Version-Release.Architecture.rpm). Note that due to
    the fact that rule implementations cannot access the contents of files,
    the "version_file" and "release_file" arguments will not create an output
    using N-V-R.A format.

    This rule only functions on UNIXy platforms. The following tools must be
    available on your system for this to function properly:

    - `rpmbuild` (as specified in `rpmbuild_path`, or available in `$PATH`)

    - GNU coreutils.  BSD coreutils may work, but are not tested.

    """,
    # @unsorted-dict-items
    attrs = {
        "rpm_name": attr.string(
            doc = """Optional; RPM name override.

            If not provided, the `name` attribute of this rule will be used
            instead.

            This influences values like the spec file name, and the name of the
            output RPM.

            """,
        ),
        "version": attr.string(
            doc = """RPM "Version" tag.

            Exactly one of `version` or `version_file` must be provided.
            """,
        ),
        "version_file": attr.label(
            doc = """File containing RPM "Version" tag.""",
            allow_single_file = True,
        ),
        "release": attr.string(
            doc = """RPM "Release" tag

            Exactly one of `release` or `release_file` must be provided.
            """,
        ),
        "release_file": attr.label(
            doc = """File containing RPM "Release" tag.""",
            allow_single_file = True,
        ),
        "group": attr.string(
            doc = """Optional; RPM "Group" tag.

            NOTE: some distributions (as of writing, Fedora > 17 and CentOS/RHEL
            > 5) have deprecated this tag.  Other distributions may require it,
            but it is harmless in any case.

            """,
        ),
        # TODO(nacl): this should be augmented to use bazel platforms, and
        # should not really set BuildArch.
        "architecture": attr.string(
            doc = """Package architecture.

            This currently sets the `BuildArch` tag, which influences the output
            architecture of the package.

            Typically, `BuildArch` only needs to be set when the package is
            known to be cross-platform (e.g. written in an interpreted
            language), or, less common, when it is known that the application is
            only valid for specific architectures.

            When no attribute is provided, this will default to your host's
            architecture.  This is usually what you want.

            """,
        ),
        "license": attr.string(
            doc = """RPM "License" tag.

            The software license for the code distributed in this package.

            The underlying RPM builder requires you to put something here; if
            your package is not going to be distributed, feel free to set this
            to something like "Internal".

            """,
            mandatory = True,
        ),
        "summary": attr.string(
            doc = """RPM "Summary" tag.

            One-line summary of this package.  Must not contain newlines.

            """,
            mandatory = True,
        ),
        "url": attr.string(
            doc = """RPM "URL" tag; this project/vendor's home on the Internet.""",
        ),
        "description": attr.string(
            doc = """Multi-line description of this package, corresponds to RPM %description.

            Exactly one of `description` or `description_file` must be provided.
            """,
        ),
        "description_file": attr.label(
            doc = """File containing a multi-line description of this package, corresponds to RPM
            %description.""",
            allow_single_file = True,
        ),
        # TODO: this isn't consumed yet
        "changelog": attr.label(
            allow_single_file = True,
        ),
        "data": attr.label_list(
            doc = """Mappings to include in this RPM.

            These are typically brought into life as `pkg_filegroup`s.
            """,
            mandatory = True,
            providers = [
                [PackageFileInfo],
                [PackageDirInfo],
            ],
        ),
        "debug": attr.bool(
            doc = """Debug the RPM helper script and RPM generation""",
            default = False,
        ),
        "pre_scriptlet": attr.string(
            doc = """RPM `%pre` scriptlet.  Currently only allowed to be a shell script.

            `pre_scriptlet` and `pre_scriptlet_file` are mutually exclusive.
            """,
        ),
        "pre_scriptlet_file": attr.label(
            doc = """File containing the RPM `%pre` scriptlet""",
            allow_single_file = True,
        ),
        "post_scriptlet": attr.string(
            doc = """RPM `%post` scriptlet.  Currently only allowed to be a shell script.

            `post_scriptlet` and `post_scriptlet_file` are mutually exclusive.
            """,
        ),
        "post_scriptlet_file": attr.label(
            doc = """File containing the RPM `%post` scriptlet""",
            allow_single_file = True,
        ),
        "preun_scriptlet": attr.string(
            doc = """RPM `%preun` scriptlet.  Currently only allowed to be a shell script.

            `preun_scriptlet` and `preun_scriptlet_file` are mutually exclusive.
            """,
        ),
        "preun_scriptlet_file": attr.label(
            doc = """File containing the RPM `%preun` scriptlet""",
            allow_single_file = True,
        ),
        "postun_scriptlet": attr.string(
            doc = """RPM `%postun` scriptlet.  Currently only allowed to be a shell script.

            `postun_scriptlet` and `postun_scriptlet_file` are mutually exclusive.
            """,
        ),
        "postun_scriptlet_file": attr.label(
            doc = """File containing the RPM `%postun` scriptlet""",
            allow_single_file = True,
        ),

        # TODO(nacl): this should be a toolchain
        "rpmbuild_path": attr.string(
            doc = """Path to a `rpmbuild` binary.""",
        ),
        "spec_template": attr.label(
            doc = """Spec file template.

            Use this if you need to add additional logic to your spec files that
            is not available by default.

            In most cases, you should not need to override this attribute.
            """,
            allow_single_file = spec_filetype,
            default = "@rules_pkg//experimental:template.spec.in",
        ),

        # Implicit dependencies.
        "_make_rpm": attr.label(
            default = Label("@rules_pkg//experimental:make_rpm"),
            cfg = "host",
            executable = True,
            allow_files = True,
        ),
    },
    executable = False,
    outputs = _pkg_rpm_outputs,
    implementation = _pkg_rpm_impl,
)
