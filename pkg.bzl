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

# Filetype to restrict inputs
tar_filetype = [".tar", ".tar.gz", ".tgz", ".tar.xz", ".tar.bz2"]
deb_filetype = [".deb", ".udeb"]

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

    # Compute the relative path
    data_path = compute_data_path(ctx.outputs.out, ctx.attr.strip_prefix)
    # Find a list of path remappings to apply.
    remap_paths = dict(ctx.attr.remap_paths)

    # Make symlinks mutable so that we can add possible python links
    symlinks = dict(ctx.attr.symlinks)

    # Package dir can be specified by a file or inlined.
    if ctx.attr.package_dir_file:
        if ctx.attr.package_dir:
            fail("Both package_dir and package_dir_file attributes were specified")
        package_dir_arg = "--directory=@" + ctx.file.package_dir_file.path
        files.append(ctx.file.package_dir_file)
    else:
        package_dir_arg = "--directory=" + ctx.attr.package_dir or "/"

    # Start building the arguments.
    args = [
        "--output=" + ctx.outputs.out.path,
        package_dir_arg,
        "--mode=" + ctx.attr.mode,
        "--owner=" + ctx.attr.owner,
        "--owner_name=" + ctx.attr.ownername,
    ]
    if ctx.attr.mtime != -1:  # Note: Must match default in rule def.
        if ctx.attr.portable_mtime:
            fail("You may not set both mtime and portable_mtime")
        args.append("--mtime=%d" % ctx.attr.mtime)
    if ctx.attr.portable_mtime:
        args.append("--mtime=portable")

    if ctx.attr.py_venv and not ctx.attr.include_runfiles:
        fail("If pkg_tar py_venv is provided include_runfiles must be True")

    venv_workspace_name = None
    venv_runfile_python_path = None
    external_venv_runfile_python_path = None
    if ctx.attr.py_venv:
        venv_workspace_name = ctx.attr.py_venv.label.workspace_name
        venv_runfile_python_path = "{}/{}/bin/python".format(venv_workspace_name, venv_workspace_name)
        external_venv_runfile_python_path = "external/{}".format(venv_runfile_python_path)
        has_correct_environment = False
        for f in ctx.attr.srcs:
            default_runfiles = f[DefaultInfo].default_runfiles
            runfile_tree_root = "{}/{}.runfiles".format(f.label.package, f.label.name)


            if external_venv_runfile_python_path in [x.path for x in default_runfiles.files.to_list()]:
                has_correct_environment = True
                full_runfile_interpreter_path = "{}/{}/{}".format(
                    ctx.attr.package_dir,
                    runfile_tree_root,
                    venv_runfile_python_path
                )
                symlinks[full_runfile_interpreter_path] = "{}/bin/python".format(
                    ctx.attr.py_venv_deploy_path)

        if not has_correct_environment:
            print("If you specify the py_venv parameter, this python target" +
                " must be built with the correct config from .bazelrc. This doesn't seem" +
                " to be the case because {} is not in any srcs' runfiles".format(venv_runfile_python_path))
            pass

    file_inputs = []
    # Add runfiles if requested
    workspace_name = (ctx.workspace_name if ctx.workspace_name else "__main__" )
    runfiles_depsets = []
    if ctx.attr.include_runfiles:
        for f in ctx.attr.srcs:
            default_runfiles = f[DefaultInfo].default_runfiles
            if default_runfiles == None:
                continue
            elif ctx.attr.include_runfile_tree:
                for runfile in default_runfiles.files.to_list():
                    runfile_tree_path = "{}/{}.runfiles".format(
                        f.label.package,
                        f.label.name)

                    strip_prefix = ctx.attr.strip_prefix
                    if strip_prefix != None and strip_prefix != "":
                        lsp = len(strip_prefix)
                        if strip_prefix[0] == "/" and strip_prefix[1:] == runfile_tree_path[:lsp-1]:
                            runfile_tree_path = runfile_tree_path[lsp-1:]
                        if strip_prefix == runfile_tree_path[0:lsp]:
                            runfile_tree_path = runfile_tree_path[lsp:]

                    # Make sure to not include the generated executable in the runfiles
                    if f.files_to_run.executable.short_path != runfile.short_path:
                        remap_paths[runfile.short_path] = runfile_tree_path + "/" + workspace_name + "/" + runfile.short_path

            runfiles_depsets.append(default_runfiles.files)
        # deduplicates files in srcs attribute and their runfiles
        file_inputs = depset(ctx.files.srcs, transitive = runfiles_depsets).to_list()
    else:
        file_inputs = ctx.files.srcs[:]

    args += [
        "--file=%s=%s" % (_quote(f.path), _remap(remap_paths, dest_path(f, data_path)))
        for f in file_inputs
    ]

    for target, f_dest_path in ctx.attr.files.items():
        target_files = target.files.to_list()
        if len(target_files) != 1:
            fail("Each input must describe exactly one file.", attr = "files")
        file_inputs += target_files
        args += ["--file=%s=%s" % (_quote(target_files[0].path), f_dest_path)]
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
    if ctx.attr.empty_files:
        args += ["--empty_file=%s" % empty_file for empty_file in ctx.attr.empty_files]
    if ctx.attr.empty_dirs:
        args += ["--empty_dir=%s" % empty_dir for empty_dir in ctx.attr.empty_dirs]
    if ctx.attr.extension:
        dotPos = ctx.attr.extension.find(".")
        if dotPos > 0:
            dotPos += 1
            args += ["--compression=%s" % ctx.attr.extension[dotPos:]]
        elif ctx.attr.extension == "tgz":
            args += ["--compression=gz"]
    args += ["--tar=" + f.path for f in ctx.files.deps]
    args += [
        "--link=%s:%s" % (_quote(k, protect = ":"), symlinks[k])
        for k in symlinks
    ]
    arg_file = ctx.actions.declare_file(ctx.label.name + ".args")
    files.append(arg_file)
    ctx.actions.write(arg_file, "\n".join(args))

    ctx.actions.run(
        mnemonic = "PackageTar",
        inputs = file_inputs + ctx.files.deps + files,
        executable = ctx.executable.build_tar,
        arguments = ["@" + arg_file.path],
        outputs = [ctx.outputs.out],
        env = {
            "LANG": "en_US.UTF-8",
            "LC_CTYPE": "UTF-8",
            "PYTHONIOENCODING": "UTF-8",
            "PYTHONUTF8": "1",
        },
        use_default_shell_env = True,
    )
    return OutputGroupInfo(out = [ctx.outputs.out])

def _pkg_deb_impl(ctx):
    """The implementation for the pkg_deb rule."""
    files = [ctx.file.data]
    args = [
        "--output=" + ctx.outputs.deb.path,
        "--changes=" + (ctx.outputs.changes.path if ctx.outputs.changes else ""),
        "--data=" + ctx.file.data.path,
        "--package=" + ctx.attr.package,
        "--architecture=" + ctx.attr.architecture,
        "--maintainer=" + ctx.attr.maintainer,
    ]
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
    args += ["--provides=" + d for d in ctx.attr.provides]
    args += ["--breaks=" + d for d in ctx.attr.breaks]
    args += ["--pre_depends=" + d for d in ctx.attr.predepends]
    args += ["--recommends=" + d for d in ctx.attr.recommends]
    args += ["--replaces=" + d for d in ctx.attr.replaces]

    outputs = [ctx.outputs.deb]
    if ctx.attr.output_changes:
        args += ["--output_changes"]
        outputs += [ctx.outputs.changes]

    ctx.actions.run(
        mnemonic = "MakeDeb",
        executable = ctx.executable.make_deb,
        arguments = args,
        inputs = files,
        outputs = outputs,
        env = {
            "LANG": "en_US.UTF-8",
            "LC_CTYPE": "UTF-8",
            "PYTHONIOENCODING": "UTF-8",
            "PYTHONUTF8": "1",
        },
    )
    ctx.actions.run_shell(
        command = "ln -s %s %s" % (ctx.outputs.deb.basename, ctx.outputs.out.path),
        inputs = [ctx.outputs.deb],
        outputs = [ctx.outputs.out],
    )
    output_groups = {"out": [ctx.outputs.out]}
    if hasattr(ctx.outputs, "deb"):
        output_groups["deb"] = [ctx.outputs.deb]
    if ctx.attr.output_changes and hasattr(ctx.outputs, "changes"):
        output_groups["changes"] = [ctx.outputs.changes]
    return OutputGroupInfo(**output_groups)

# A rule for creating a tar file, see README.md
pkg_tar_impl = rule(
    implementation = _pkg_tar_impl,
    attrs = {
        "strip_prefix": attr.string(),
        "package_dir": attr.string(),
        "package_dir_file": attr.label(allow_single_file = True),
        "deps": attr.label_list(allow_files = tar_filetype),
        "srcs": attr.label_list(allow_files = True),
        "files": attr.label_keyed_string_dict(allow_files = True),
        "mode": attr.string(default = "0555"),
        "modes": attr.string_dict(),
        "mtime": attr.int(default = -1),
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

        # Custom atrributes
        "include_runfile_tree": attr.bool(default = False),
        "py_venv": attr.label(allow_files = True),
        "py_venv_deploy_path": attr.string(default=""),

        # Outputs
        "out": attr.output(),

        # Implicit dependencies.
        "build_tar": attr.label(
            default = Label("@rules_pkg//:build_tar"),
            cfg = "host",
            executable = True,
            allow_files = True,
        ),
    },
)

def pkg_tar(**kwargs):
    # Compatibility with older versions of pkg_tar that define files as
    # a flat list of labels.
    if "srcs" not in kwargs:
        if "files" in kwargs:
            if not hasattr(kwargs["files"], "items"):
                label = "%s//%s:%s" % (native.repository_name(), native.package_name(), kwargs["name"])
                print("%s: you provided a non dictionary to the pkg_tar `files` attribute. " % (label,) +
                      "This attribute was renamed to `srcs`. " +
                      "Consider renaming it in your BUILD file.")
                kwargs["srcs"] = kwargs.pop("files")
    extension = kwargs.get("extension") or "tar"
    pkg_tar_impl(
        out = kwargs["name"] + "." + extension,
        **kwargs
    )

# A rule for creating a deb file, see README.md
pkg_deb_impl = rule(
    implementation = _pkg_deb_impl,
    attrs = {
        "data": attr.label(mandatory = True, allow_single_file = tar_filetype),
        "package": attr.string(mandatory = True),
        "architecture": attr.string(default = "all"),
        "distribution": attr.string(default = "unstable"),
        "urgency": attr.string(default = "medium"),
        "maintainer": attr.string(mandatory = True),
        "preinst": attr.label(allow_single_file = True),
        "postinst": attr.label(allow_single_file = True),
        "prerm": attr.label(allow_single_file = True),
        "postrm": attr.label(allow_single_file = True),
        "config": attr.label(allow_single_file = True),
        "templates": attr.label(allow_single_file = True),
        "conffiles_file": attr.label(allow_single_file = True),
        "conffiles": attr.string_list(default = []),
        "version_file": attr.label(allow_single_file = True),
        "version": attr.string(),
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
        "provides": attr.string_list(default = []),
        "predepends": attr.string_list(default = []),
        "recommends": attr.string_list(default = []),
        "replaces": attr.string_list(default = []),
        "output_changes" : attr.bool(default = False),

        # Outputs.
        "out": attr.output(mandatory = True),
        "deb": attr.output(mandatory = True),
        "changes": attr.output(mandatory = False),

        # Implicit dependencies.
        "make_deb": attr.label(
            default = Label("@rules_pkg//:make_deb"),
            cfg = "host",
            executable = True,
            allow_files = True,
        ),
    },
)

def pkg_deb(name, package, **kwargs):
    """Creates a deb file. See pkg_deb_impl."""
    version = kwargs.get("version") or ""
    architecture = kwargs.get("architecture") or "all"
    out_deb = "%s_%s_%s.deb" % (package, version, architecture)
    should_output_changes = kwargs.get("output_changes") == True
    out_changes = None
    if should_output_changes:
        out_changes = "%s_%s_%s.changes" % (package, version, architecture)
    pkg_deb_impl(
        name = name,
        package = package,
        out = name + ".deb",
        deb = out_deb,
        changes = out_changes,
        **kwargs
    )

def _format_zip_file_arg(f):
    return "%s=%s" % (_quote(f.path), dest_path(f, strip_prefix = None))

def _pkg_zip_impl(ctx):
    args = ctx.actions.args()

    args.add("-o", ctx.outputs.out.path)
    args.add("-d", ctx.attr.package_dir)
    args.add("-t", ctx.attr.timestamp)

    args.add_all(
        ctx.files.srcs,
        map_each = _format_zip_file_arg,
    )

    args.set_param_file_format("multiline")
    args.use_param_file("@%s")

    ctx.actions.run(
        mnemonic = "PackageZip",
        inputs = ctx.files.srcs,
        executable = ctx.executable.build_zip,
        arguments = [args],
        outputs = [ctx.outputs.out],
        env = {
            "LANG": "en_US.UTF-8",
            "LC_CTYPE": "UTF-8",
            "PYTHONIOENCODING": "UTF-8",
            "PYTHONUTF8": "1",
        },
        use_default_shell_env = True,
    )
    return OutputGroupInfo(out=[ctx.outputs.out])

pkg_zip_impl = rule(
    implementation = _pkg_zip_impl,
    attrs = {
        "extension": attr.string(default = "zip"),
        "srcs": attr.label_list(allow_files = True),
        "package_dir": attr.string(default = "/"),
        "timestamp": attr.int(default = 315532800),
        "out": attr.output(),
        # Implicit dependencies.
        "build_zip": attr.label(
            default = Label("@rules_pkg//:build_zip"),
            cfg = "host",
            executable = True,
            allow_files = True,
        ),
    },
)

def pkg_zip(name, **kwargs):
    extension = kwargs.get("extension") or "zip"

    pkg_zip_impl(
        name = name,
        out = name + "." + extension,
        **kwargs
    )
