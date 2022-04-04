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
"""Rules for making .tar files."""

load("//pkg:path.bzl", "compute_data_path", "dest_path")
load("//pkg:providers.bzl", "PackageArtifactInfo", "PackageVariablesInfo")
load(
    "//pkg/private:pkg_files.bzl",
    "add_directory",
    "add_empty_file",
    "add_label_list",
    "add_single_file",
    "add_symlink",
    "add_tree_artifact",
    "process_src",
    "write_manifest",
)
load("//pkg/private:util.bzl", "setup_output_files", "substitute_package_variables")

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
_DEFAULT_MTIME = -1
_stamp_condition = str(Label("//pkg/private:private_stamp_detect"))

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

    # Start building the arguments.
    args = ctx.actions.args()
    args.add("--output", output_file.path)
    args.add("--mode", ctx.attr.mode)
    args.add("--owner", ctx.attr.owner)
    args.add("--owner_name", ctx.attr.ownername)

    # Package dir can be specified by a file or inlined.
    if ctx.attr.package_dir_file:
        if ctx.attr.package_dir:
            fail("Both package_dir and package_dir_file attributes were specified")
        args.add("--directory", "@" + ctx.file.package_dir_file.path)
        files.append(ctx.file.package_dir_file)
    else:
        package_dir_expanded = substitute_package_variables(ctx, ctx.attr.package_dir)
        args.add("--directory", package_dir_expanded or "/")

    if ctx.executable.compressor:
        args.add("--compressor", "%s %s" % (ctx.executable.compressor.path, ctx.attr.compressor_args))
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
                    args.add("--compression", compression)
                else:
                    fail("Unsupported compression: '%s'" % compression)

    if ctx.attr.mtime != _DEFAULT_MTIME:
        if ctx.attr.portable_mtime:
            fail("You may not set both mtime and portable_mtime")
        args.add("--mtime", "%d" % ctx.attr.mtime)
    if ctx.attr.portable_mtime:
        args.add("--mtime", "portable")

    # Now we begin processing the files.
    file_deps = []  # inputs we depend on
    content_map = {}  # content handled in the manifest

    # Start with all the pkg_* inputs
    for src in ctx.attr.srcs:
        if not process_src(
            content_map,
            file_deps,
            src = src,
            origin = src.label,
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
                    add_tree_artifact(content_map, d_path, f, src.label)
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
        for key in ctx.attr.modes:
            args.add("--modes", "%s=%s" % (_quote(key), ctx.attr.modes[key]))
    if ctx.attr.owners:
        for key in ctx.attr.owners:
            args.add("--owners", "%s=%s" % (_quote(key), ctx.attr.owners[key]))
    if ctx.attr.ownernames:
        for key in ctx.attr.ownernames:
            args.add(
                "--owner_names",
                "%s=%s" % (_quote(key), ctx.attr.ownernames[key]),
            )
    for empty_file in ctx.attr.empty_files:
        add_empty_file(content_map, empty_file, ctx.label)
    for empty_dir in ctx.attr.empty_dirs or []:
        add_directory(content_map, empty_dir, ctx.label)
    for f in ctx.files.deps:
        args.add("--tar", f.path)
    for link in ctx.attr.symlinks:
        add_symlink(
            content_map,
            link,
            ctx.attr.symlinks[link],
            ctx.label,
        )
    if ctx.attr.stamp == 1 or (ctx.attr.stamp == -1 and
                               ctx.attr.private_stamp_detect):
        args.add("--stamp_from", ctx.version_file.path)
        files.append(ctx.version_file)

    file_inputs = depset(transitive = file_deps)
    manifest_file = ctx.actions.declare_file(ctx.label.name + ".manifest")
    files.append(manifest_file)
    write_manifest(ctx, manifest_file, content_map)
    args.add("--manifest", manifest_file.path)

    args.set_param_file_format("flag_per_line")
    args.use_param_file("@%s", use_always = False)

    ctx.actions.run(
        mnemonic = "PackageTar",
        progress_message = "Writing: %s" % output_file.path,
        inputs = file_inputs.to_list() + ctx.files.deps + files,
        tools = [ctx.executable.compressor] if ctx.executable.compressor else [],
        executable = ctx.executable.build_tar,
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
            file = output_file,
            file_name = output_name,
        ),
    ]

# A rule for creating a tar file, see README.md
pkg_tar_impl = rule(
    implementation = _pkg_tar_impl,
    attrs = {
        "strip_prefix": attr.string(),
        "package_dir": attr.string(
            doc = """Prefix to be prepend to all paths written."""
        ),
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
            doc = """Enable file time stamping.  Possible values:
<li>stamp = 1: Use the time of the build as the modification time of each file in the archive.
<li>stamp = 0: Use an "epoch" time for the modification time of each file. This gives good build result caching.
<li>stamp = -1: Control the chosen modification time using the --[no]stamp flag.
""",
            default = 0,
        ),
        # Is --stamp set on the command line?
        # TODO(https://github.com/bazelbuild/rules_pkg/issues/340): Remove this.
        "private_stamp_detect": attr.bool(default = False),

        # Implicit dependencies.
        "build_tar": attr.label(
            default = Label("//pkg/private/tar:build_tar"),
            cfg = "exec",
            executable = True,
            allow_files = True,
        ),
    },
    provides = [PackageArtifactInfo],
)

def pkg_tar(name, **kwargs):
    """Creates a .tar file. See pkg_tar_impl.

    @wraps(pkg_tar_impl)
    """
    # Compatibility with older versions of pkg_tar that define files as
    # a flat list of labels.
    if "srcs" not in kwargs:
        if "files" in kwargs:
            if not hasattr(kwargs["files"], "items"):
                label = "%s//%s:%s" % (native.repository_name(), native.package_name(), name)

                # buildifier: disable=print
                print("%s: you provided a non dictionary to the pkg_tar `files` attribute. " % (label,) +
                      "This attribute was renamed to `srcs`. " +
                      "Consider renaming it in your BUILD file.")
                kwargs["srcs"] = kwargs.pop("files")
    extension = kwargs.get("extension") or "tar"
    if extension[0] == ".":
        extension = extension[1:]
    pkg_tar_impl(
        name = name,
        out = kwargs.pop("out", None) or (name + "." + extension),
        private_stamp_detect = select({
            _stamp_condition: True,
            "//conditions:default": False,
        }),
        **kwargs
    )
