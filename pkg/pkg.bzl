# Copyright 2015 The Bazel Authors. All rights reserved.
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
"""Rules for manipulation of various packaging."""

load(":path.bzl", "compute_data_path", "dest_path")
load(
    ":providers.bzl",
    "PackageArtifactInfo",
    "PackageFilegroupInfo",
    "PackageFilesInfo",
    "PackageVariablesInfo",
)
load("//private:util.bzl", "setup_output_files", "substitute_package_variables")
load(
    "//private:pkg_files.bzl",
    "add_directory",
    "add_empty_file",
    "add_label_list",
    "add_single_file",
    "add_symlink",
    "add_tree_artifact",
    "process_src",
    "write_manifest",
)

# TODO(aiuto): Figure  out how to get this from the python toolchain.
# See check for lzma in archive.py for a hint at a method.
HAS_XZ_SUPPORT = True

# Filetype to restrict inputs
tar_filetype = (
    [".tar", ".tar.gz", ".tgz", ".tar.bz2", "tar.xz"] if HAS_XZ_SUPPORT else [".tar", ".tar.gz", ".tgz", ".tar.bz2"]
)
SUPPORTED_TAR_COMPRESSIONS = (
    ["", "gz", "bz2", "xz"] if HAS_XZ_SUPPORT else ["", "gz", "bz2"]
)
deb_filetype = [".deb", ".udeb"]
_DEFAULT_MTIME = -1
_stamp_condition = str(Label("//private:private_stamp_detect"))

def _remap(remap_paths, path):
    """If path starts with a key in remap_paths, rewrite it."""
    for prefix, replacement in remap_paths.items():
        if path.startswith(prefix):
            return replacement + path[len(prefix):]
    return path

def _quote(filename, protect = "="):
    """Quote the filename, by escaping = by \\= and \\ by \\\\"""
    return filename.replace("\\", "\\\\").replace(protect, "\\" + protect)

def _pkg_tar_impl(ctx):
    """Implementation of the pkg_tar rule."""

    # Files needed by rule implementation at runtime
    files = []

    outputs, output_file, output_name = setup_output_files(ctx)

    # Compute the relative path
    data_path = compute_data_path(ctx, ctx.attr.strip_prefix)
    data_path_without_prefix = compute_data_path(ctx, ".")

    # Find a list of path remappings to apply.
    remap_paths = ctx.attr.remap_paths

    # Package dir can be specified by a file or inlined.
    if ctx.attr.package_dir_file:
        if ctx.attr.package_dir:
            fail("Both package_dir and package_dir_file attributes were specified")
        package_dir_arg = "--directory=@" + ctx.file.package_dir_file.path
        files.append(ctx.file.package_dir_file)
    else:
        package_dir_expanded = substitute_package_variables(ctx, ctx.attr.package_dir)
        package_dir_arg = "--directory=" + package_dir_expanded or "/"

    # Start building the arguments.
    args = [
        "--root_directory=" + ctx.attr.package_base,
        "--output=" + output_file.path,
        package_dir_arg,
        "--mode=" + ctx.attr.mode,
        "--owner=" + ctx.attr.owner,
        "--owner_name=" + ctx.attr.ownername,
    ]
    if ctx.executable.compressor:
        args.append("--compressor=%s %s" % (ctx.executable.compressor.path, ctx.attr.compressor_args))
    else:
        extension = ctx.attr.extension
        if extension and extension != "tar":
            compression = None
            dot_pos = ctx.attr.extension.rfind(".")
            if dot_pos >= 0:
                compression = ctx.attr.extension[dot_pos + 1:]
            else:
                compression = ctx.attr.extension
            if compression == "tgz":
                compression = "gz"
            if compression:
                if compression in SUPPORTED_TAR_COMPRESSIONS:
                    args += ["--compression=%s" % compression]
                else:
                    fail("Unsupported compression: '%s'" % compression)

    if ctx.attr.mtime != _DEFAULT_MTIME:
        if ctx.attr.portable_mtime:
            fail("You may not set both mtime and portable_mtime")
        args.append("--mtime=%d" % ctx.attr.mtime)
    if ctx.attr.portable_mtime:
        args.append("--mtime=portable")

    # Now we begin processing the files.
    file_deps = []  # inputs we depend on
    content_map = {}  # content handled in the manifest

    # Start with all the pkg_* inputs
    for src in ctx.attr.srcs:
        # Gather the files for every srcs entry here, even if it is not from
        # a pkg_* rule.
        if DefaultInfo in src:
            file_deps.append(src[DefaultInfo].files)
        if not process_src(
            content_map,
            src,
            src.label,
            default_mode = None,
            default_user = None,
            default_group = None,
        ):
            src_files = src[DefaultInfo].files.to_list()
            if ctx.attr.include_runfiles:
                runfiles = src[DefaultInfo].default_runfiles
                if runfiles:
                     file_deps.append(runfiles.files)
                     src_files.extend(runfiles.files.to_list())
            # Add in the files of srcs which are not pkg_* types
            for f in src_files:
                d_path = dest_path(f, data_path, data_path_without_prefix)
                if f.is_directory:
                    # Tree artifacts need a name, but the name is never really
                    # the important part. The likely behavior people want is
                    # just the content, so we strip the directory name.
                    dest = "/".join(d_path.split("/")[0:-1])
                    add_tree_artifact(content_map, dest, f, src.label)
                else:
                    # Note: This extra remap is the bottleneck preventing this
                    # large block from being a utility method as shown below.
                    # Should we disallow mixing pkg_files in srcs with remap?
                    # I am fine with that if it makes the code more readable.
                    dest = _remap(remap_paths, d_path)
                    add_single_file(content_map, dest, f, src.label)

    # TODO(aiuto): I want the code to look like this, but we don't have lambdas.
    # transform_path = lambda f: _remap(
    #    remap_paths, dest_path(f, data_path, data_path_without_prefix))
    # add_label_list(ctx, content_map, file_deps, ctx.attr.srcs, transform_path)

    # The files attribute is a map of labels to destinations. We can add them
    # directly to the content map.
    for target, f_dest_path in ctx.attr.files.items():
        target_files = target.files.to_list()
        if len(target_files) != 1:
            fail("Each input must describe exactly one file.", attr = "files")
        file_deps.append(depset([target_files[0]]))
        add_single_file(
            content_map,
            f_dest_path,
            target_files[0],
            target.label,
        )

    if ctx.attr.modes:
        args += [
            "--modes=%s=%s" % (_quote(key), ctx.attr.modes[key])
            for key in ctx.attr.modes
        ]
    if ctx.attr.owners:
        args += [
            "--owners=%s=%s" % (_quote(key), ctx.attr.owners[key])
            for key in ctx.attr.owners
        ]
    if ctx.attr.ownernames:
        args += [
            "--owner_names=%s=%s" % (_quote(key), ctx.attr.ownernames[key])
            for key in ctx.attr.ownernames
        ]
    for empty_file in ctx.attr.empty_files:
        add_empty_file(content_map, empty_file, ctx.label)
    for empty_dir in ctx.attr.empty_dirs or []:
        add_directory(content_map, empty_dir, ctx.label)
    args += ["--tar=" + f.path for f in ctx.files.deps]
    for link in ctx.attr.symlinks:
        add_symlink(
            content_map,
            link,
            ctx.attr.symlinks[link],
            ctx.label,
        )
    if ctx.attr.stamp == 1 or (ctx.attr.stamp == -1 and
                               ctx.attr.private_stamp_detect):
        args.append("--stamp_from=%s" % ctx.version_file.path)
        files.append(ctx.version_file)

    file_inputs = depset(transitive = file_deps)
    manifest_file = ctx.actions.declare_file(ctx.label.name + ".manifest")
    files.append(manifest_file)
    write_manifest(ctx, manifest_file, content_map)
    args.append("--manifest=%s" % manifest_file.path)

    arg_file = ctx.actions.declare_file(ctx.label.name + ".args")
    files.append(arg_file)
    ctx.actions.write(arg_file, "\n".join(args))

    ctx.actions.run(
        mnemonic = "PackageTar",
        progress_message = "Writing: %s" % output_file.path,
        inputs = file_inputs.to_list() + ctx.files.deps + files,
        tools = [ctx.executable.compressor] if ctx.executable.compressor else [],
        executable = ctx.executable.build_tar,
        arguments = ["@" + arg_file.path],
        outputs = [output_file],
        env = {
            "LANG": "en_US.UTF-8",
            "LC_CTYPE": "UTF-8",
            "PYTHONIOENCODING": "UTF-8",
            "PYTHONUTF8": "1",
        },
        use_default_shell_env = True,
    )
    return [
        DefaultInfo(
            files = depset([output_file]),
            runfiles = ctx.runfiles(files = outputs),
        ),
        PackageArtifactInfo(
            label = ctx.label.name,
            file_name = output_name,
        ),
    ]

def _pkg_deb_impl(ctx):
    """The implementation for the pkg_deb rule."""

    package_file_name = ctx.attr.package_file_name
    if not package_file_name:
        package_file_name = "%s_%s_%s.deb" % (
            ctx.attr.package,
            ctx.attr.version,
            ctx.attr.architecture,
        )

    outputs, output_file, output_name = setup_output_files(
        ctx,
        package_file_name = package_file_name,
    )

    changes_file = ctx.actions.declare_file(output_name.split(".")[0] + ".changes")
    outputs.append(changes_file)

    files = [ctx.file.data]
    args = [
        "--output=" + output_file.path,
        "--changes=" + changes_file.path,
        "--data=" + ctx.file.data.path,
        "--package=" + ctx.attr.package,
        "--maintainer=" + ctx.attr.maintainer,
    ]

    # Version and description can be specified by a file or inlined
    if ctx.attr.architecture_file:
        if ctx.attr.architecture != "all":
            fail("Both architecture and architecture_file attributes were specified")
        args += ["--architecture=@" + ctx.file.architecture_file.path]
        files += [ctx.file.architecture_file]
    else:
        args += ["--architecture=" + ctx.attr.architecture]

    if ctx.attr.preinst:
        args += ["--preinst=@" + ctx.file.preinst.path]
        files += [ctx.file.preinst]
    if ctx.attr.postinst:
        args += ["--postinst=@" + ctx.file.postinst.path]
        files += [ctx.file.postinst]
    if ctx.attr.prerm:
        args += ["--prerm=@" + ctx.file.prerm.path]
        files += [ctx.file.prerm]
    if ctx.attr.postrm:
        args += ["--postrm=@" + ctx.file.postrm.path]
        files += [ctx.file.postrm]
    if ctx.attr.config:
        args += ["--config=@" + ctx.file.config.path]
        files += [ctx.file.config]
    if ctx.attr.templates:
        args += ["--templates=@" + ctx.file.templates.path]
        files += [ctx.file.templates]
    if ctx.attr.triggers:
        args += ["--triggers=@" + ctx.file.triggers.path]
        files += [ctx.file.triggers]

    # Conffiles can be specified by a file or a string list
    if ctx.attr.conffiles_file:
        if ctx.attr.conffiles:
            fail("Both conffiles and conffiles_file attributes were specified")
        args += ["--conffile=@" + ctx.file.conffiles_file.path]
        files += [ctx.file.conffiles_file]
    elif ctx.attr.conffiles:
        args += ["--conffile=%s" % cf for cf in ctx.attr.conffiles]

    # Version and description can be specified by a file or inlined
    if ctx.attr.version_file:
        if ctx.attr.version:
            fail("Both version and version_file attributes were specified")
        args += ["--version=@" + ctx.file.version_file.path]
        files += [ctx.file.version_file]
    elif ctx.attr.version:
        args += ["--version=" + ctx.attr.version]
    else:
        fail("Neither version_file nor version attribute was specified")

    if ctx.attr.description_file:
        if ctx.attr.description:
            fail("Both description and description_file attributes were specified")
        args += ["--description=@" + ctx.file.description_file.path]
        files += [ctx.file.description_file]
    elif ctx.attr.description:
        args += ["--description=" + ctx.attr.description]
    else:
        fail("Neither description_file nor description attribute was specified")

    # Built using can also be specified by a file or inlined (but is not mandatory)
    if ctx.attr.built_using_file:
        if ctx.attr.built_using:
            fail("Both build_using and built_using_file attributes were specified")
        args += ["--built_using=@" + ctx.file.built_using_file.path]
        files += [ctx.file.built_using_file]
    elif ctx.attr.built_using:
        args += ["--built_using=" + ctx.attr.built_using]

    if ctx.attr.depends_file:
        if ctx.attr.depends:
            fail("Both depends and depends_file attributes were specified")
        args += ["--depends=@" + ctx.file.depends_file.path]
        files += [ctx.file.depends_file]
    elif ctx.attr.depends:
        args += ["--depends=" + d for d in ctx.attr.depends]

    if ctx.attr.priority:
        args += ["--priority=" + ctx.attr.priority]
    if ctx.attr.section:
        args += ["--section=" + ctx.attr.section]
    if ctx.attr.homepage:
        args += ["--homepage=" + ctx.attr.homepage]

    args += ["--distribution=" + ctx.attr.distribution]
    args += ["--urgency=" + ctx.attr.urgency]
    args += ["--suggests=" + d for d in ctx.attr.suggests]
    args += ["--enhances=" + d for d in ctx.attr.enhances]
    args += ["--conflicts=" + d for d in ctx.attr.conflicts]
    args += ["--breaks=" + d for d in ctx.attr.breaks]
    args += ["--pre_depends=" + d for d in ctx.attr.predepends]
    args += ["--recommends=" + d for d in ctx.attr.recommends]
    args += ["--replaces=" + d for d in ctx.attr.replaces]
    args += ["--provides=" + d for d in ctx.attr.provides]

    ctx.actions.run(
        mnemonic = "MakeDeb",
        executable = ctx.executable.make_deb,
        arguments = args,
        inputs = files,
        outputs = [output_file, changes_file],
        env = {
            "LANG": "en_US.UTF-8",
            "LC_CTYPE": "UTF-8",
            "PYTHONIOENCODING": "UTF-8",
            "PYTHONUTF8": "1",
        },
    )
    output_groups = {
        "out": [ctx.outputs.out],
        "deb": [output_file],
        "changes": [changes_file],
    }
    return [
        OutputGroupInfo(**output_groups),
        DefaultInfo(
            files = depset([output_file]),
            runfiles = ctx.runfiles(files = outputs),
        ),
        PackageArtifactInfo(
            label = ctx.label.name,
            file_name = output_name,
        ),
    ]

# A rule for creating a tar file, see README.md
pkg_tar_impl = rule(
    implementation = _pkg_tar_impl,
    attrs = {
        "strip_prefix": attr.string(),
        "package_base": attr.string(default = "./"),
        "package_dir": attr.string(),
        "package_dir_file": attr.label(allow_single_file = True),
        "deps": attr.label_list(allow_files = tar_filetype),
        "srcs": attr.label_list(allow_files = True),
        "files": attr.label_keyed_string_dict(allow_files = True),
        "mode": attr.string(default = "0555"),
        "modes": attr.string_dict(),
        "mtime": attr.int(default = _DEFAULT_MTIME),
        "portable_mtime": attr.bool(default = True),
        "owner": attr.string(default = "0.0"),
        "ownername": attr.string(default = "."),
        "owners": attr.string_dict(),
        "ownernames": attr.string_dict(),
        "extension": attr.string(default = "tar"),
        "symlinks": attr.string_dict(),
        "empty_files": attr.string_list(),
        "include_runfiles": attr.bool(),
        "empty_dirs": attr.string_list(),
        "remap_paths": attr.string_dict(),
        "compressor": attr.label(executable = True, cfg = "exec"),
        "compressor_args": attr.string(),

        # Common attributes
        "out": attr.output(mandatory = True),
        "package_file_name": attr.string(doc = "See Common Attributes"),
        "package_variables": attr.label(
            doc = "See Common Attributes",
            providers = [PackageVariablesInfo],
        ),
        "stamp": attr.int(
            doc = """Enable file time stamping.  Possible values:<ul>
<li>stamp = 1: Use the time of the build as the modification time of each file in the archive.</li>
<li>stamp = 0: Use an "epoch" time for the modification time of each file. This gives good build result caching.</li>
<li>stamp = -1: Control the chosen modification time using the --[no]stamp flag.</li>
</ul>""",
            default = 0,
        ),
        # Is --stamp set on the command line?
        # TODO(https://github.com/bazelbuild/rules_pkg/issues/340): Remove this.
        "private_stamp_detect": attr.bool(default = False),

        # Implicit dependencies.
        "build_tar": attr.label(
            default = Label("//private:build_tar"),
            cfg = "exec",
            executable = True,
            allow_files = True,
        ),
    },
    provides = [PackageArtifactInfo],
)

def pkg_tar(name, **kwargs):
    """Creates a .tar file. See pkg_tar_impl."""

    # Compatibility with older versions of pkg_tar that define files as
    # a flat list of labels.
    if "srcs" not in kwargs:
        if "files" in kwargs:
            if not hasattr(kwargs["files"], "items"):
                label = "%s//%s:%s" % (native.repository_name(), native.package_name(), kwargs["name"])

                # buildifier: disable=print
                print("%s: you provided a non dictionary to the pkg_tar `files` attribute. " % (label,) +
                      "This attribute was renamed to `srcs`. " +
                      "Consider renaming it in your BUILD file.")
                kwargs["srcs"] = kwargs.pop("files")
    archive_name = kwargs.pop("archive_name", None)
    extension = kwargs.get("extension") or "tar"
    if extension[0] == ".":
        extension = extension[1:]
    if archive_name:
        if kwargs.get("package_file_name"):
            fail("You may not set both 'archive_name' and 'package_file_name'.")

        # buildifier: disable=print
        print("archive_name is deprecated. Use package_file_name instead.")
        kwargs["package_file_name"] = archive_name + "." + extension
    pkg_tar_impl(
        name = name,
        out = kwargs.pop("out", None) or (name + "." + extension),
        private_stamp_detect = select({
            _stamp_condition: True,
            "//conditions:default": False,
        }),
        **kwargs
    )

# A rule for creating a deb file, see README.md
pkg_deb_impl = rule(
    implementation = _pkg_deb_impl,
    attrs = {
        "data": attr.label(mandatory = True, allow_single_file = tar_filetype),
        "package": attr.string(
            doc = "Package name",
            mandatory = True,
        ),
        "architecture_file": attr.label(
            doc = """File that contains the package architecture.
            Must not be used with architecture.""",
            allow_single_file = True,
        ),
        "architecture": attr.string(
            default = "all",
            doc = """Package architecture. Must not be used with architecture_file.""",
        ),
        "distribution": attr.string(default = "unstable"),
        "urgency": attr.string(default = "medium"),
        "maintainer": attr.string(mandatory = True),
        "preinst": attr.label(allow_single_file = True),
        "postinst": attr.label(allow_single_file = True),
        "prerm": attr.label(allow_single_file = True),
        "postrm": attr.label(allow_single_file = True),
        "config": attr.label(allow_single_file = True),
        "templates": attr.label(allow_single_file = True),
        "triggers": attr.label(allow_single_file = True),
        "conffiles_file": attr.label(allow_single_file = True),
        "conffiles": attr.string_list(default = []),
        "version_file": attr.label(
            doc = """File that contains the package version.
            Must not be used with version.""",
            allow_single_file = True,
        ),
        "version": attr.string(
            doc = """Package version. Must not be used with version_file.""",
        ),
        "description_file": attr.label(allow_single_file = True),
        "description": attr.string(),
        "built_using_file": attr.label(allow_single_file = True),
        "built_using": attr.string(),
        "priority": attr.string(),
        "section": attr.string(),
        "homepage": attr.string(),
        "depends": attr.string_list(default = []),
        "depends_file": attr.label(allow_single_file = True),
        "suggests": attr.string_list(default = []),
        "enhances": attr.string_list(default = []),
        "breaks": attr.string_list(default = []),
        "conflicts": attr.string_list(default = []),
        "predepends": attr.string_list(default = []),
        "recommends": attr.string_list(default = []),
        "replaces": attr.string_list(default = []),
        "provides": attr.string_list(default = []),

        # Common attributes
        "out": attr.output(mandatory = True),
        "package_file_name": attr.string(doc = "See Common Attributes"),
        "package_variables": attr.label(
            doc = "See Common Attributes",
            providers = [PackageVariablesInfo],
        ),

        # Implicit dependencies.
        "make_deb": attr.label(
            default = Label("//private:make_deb"),
            cfg = "exec",
            executable = True,
            allow_files = True,
        ),
    },
    provides = [PackageArtifactInfo],
)

def pkg_deb(name, archive_name = None, **kwargs):
    """Creates a deb file. See pkg_deb_impl."""
    if archive_name:
        # buildifier: disable=print
        print("'archive_name' is deprecated. Use 'package_file_name' or 'out' to name the output.")
        if kwargs.get("package_file_name"):
            fail("You may not set both 'archive_name' and 'package_file_name'.")
    pkg_deb_impl(
        name = name,
        out = (archive_name or name) + ".deb",
        **kwargs
    )

def _pkg_zip_impl(ctx):
    outputs, output_file, output_name = setup_output_files(ctx)

    args = ctx.actions.args()
    args.add("-o", output_file.path)
    args.add("-d", ctx.attr.package_dir)
    args.add("-t", ctx.attr.timestamp)
    args.add("-m", ctx.attr.mode)
    inputs = []
    if ctx.attr.stamp == 1 or (ctx.attr.stamp == -1 and
                               ctx.attr.private_stamp_detect):
        args.add("--stamp_from", ctx.version_file.path)
        inputs.append(ctx.version_file)

    data_path = compute_data_path(ctx, ctx.attr.strip_prefix)
    data_path_without_prefix = compute_data_path(ctx, ".")

    content_map = {}  # content handled in the manifest
    # TODO(aiuto): Refactor this loop out of pkg_tar and pkg_zip into a helper
    # that both can use.
    for src in ctx.attr.srcs:
        # Gather the files for every srcs entry here, even if it is not from
        # a pkg_* rule.
        if DefaultInfo in src:
            inputs.extend(src[DefaultInfo].files.to_list())
        if not process_src(
            content_map,
            src,
            src.label,
            default_mode = None,
            default_user = None,
            default_group = None,
        ):
            # Add in the files of srcs which are not pkg_* types
            for f in src.files.to_list():
                d_path = dest_path(f, data_path, data_path_without_prefix)
                if f.is_directory:
                    # Tree artifacts need a name, but the name is never really
                    # the important part. The likely behavior people want is
                    # just the content, so we strip the directory name.
                    dest = '/'.join(d_path.split('/')[0:-1])
                    add_tree_artifact(content_map, dest, f, src.label)
                else:
                    add_single_file(content_map, d_path, f, src.label)

    manifest_file = ctx.actions.declare_file(ctx.label.name + ".manifest")
    inputs.append(manifest_file)
    write_manifest(ctx, manifest_file, content_map)
    args.add("--manifest", manifest_file.path)
    args.set_param_file_format("multiline")
    args.use_param_file("@%s")

    ctx.actions.run(
        mnemonic = "PackageZip",
        inputs = ctx.files.srcs + inputs,
        executable = ctx.executable._build_zip,
        arguments = [args],
        outputs = [output_file],
        env = {
            "LANG": "en_US.UTF-8",
            "LC_CTYPE": "UTF-8",
            "PYTHONIOENCODING": "UTF-8",
            "PYTHONUTF8": "1",
        },
        use_default_shell_env = True,
    )
    return [
        DefaultInfo(
            files = depset([output_file]),
            runfiles = ctx.runfiles(files = outputs),
        ),
        PackageArtifactInfo(
            label = ctx.label.name,
            file_name = output_name,
        ),
    ]

pkg_zip_impl = rule(
    implementation = _pkg_zip_impl,
    attrs = {
        "mode": attr.string(default = "0555"),
        "package_dir": attr.string(default = "/"),
        "srcs": attr.label_list(allow_files = True),
        "strip_prefix": attr.string(),
        "timestamp": attr.int(default = 315532800),

        # Common attributes
        "out": attr.output(mandatory = True),
        "package_file_name": attr.string(doc = "See Common Attributes"),
        "package_variables": attr.label(
            doc = "See Common Attributes",
            providers = [PackageVariablesInfo],
        ),
        "stamp": attr.int(
            doc = """Enable file time stamping.  Possible values:<ul>
<li>stamp = 1: Use the time of the build as the modification time of each file in the archive.</li>
<li>stamp = 0: Use an "epoch" time for the modification time of each file. This gives good build result caching.</li>
<li>stamp = -1: Control the chosen modification time using the --[no]stamp flag.</li>
</ul>""",
            default = 0,
        ),

        # Is --stamp set on the command line?
        # TODO(https://github.com/bazelbuild/rules_pkg/issues/340): Remove this.
        "private_stamp_detect": attr.bool(default = False),

        # Implicit dependencies.
        "_build_zip": attr.label(
            default = Label("//private:build_zip"),
            cfg = "exec",
            executable = True,
            allow_files = True,
        ),
    },
    provides = [PackageArtifactInfo],
)

def pkg_zip(name, **kwargs):
    """Creates a .zip file. See pkg_zip_impl."""
    extension = kwargs.pop("extension", None)
    if extension:
        # buildifier: disable=print
        print("'extension' is deprecated. Use 'package_file_name' or 'out' to name the output.")
    else:
        extension = "zip"
    archive_name = kwargs.pop("archive_name", None)
    if archive_name:
        if kwargs.get("package_file_name"):
            fail("You may not set both 'archive_name' and 'package_file_name'.")

        # buildifier: disable=print
        print("archive_name is deprecated. Use package_file_name instead.")
        kwargs["package_file_name"] = archive_name + "." + extension
    else:
        archive_name = name
    pkg_zip_impl(
        name = name,
        out = archive_name + "." + extension,
        private_stamp_detect = select({
            _stamp_condition: True,
            "//conditions:default": False,
        }),
        **kwargs
    )
