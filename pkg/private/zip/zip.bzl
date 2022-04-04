# Copyright 2021 The Bazel Authors. All rights reserved.
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

load("//pkg:path.bzl", "compute_data_path", "dest_path")
load(
    "//pkg:providers.bzl",
    "PackageArtifactInfo",
    "PackageVariablesInfo",
)
load("//pkg/private:util.bzl", "setup_output_files")
load(
    "//pkg/private:pkg_files.bzl",
    "add_label_list",
    "write_manifest",
)

_stamp_condition = str(Label("//pkg/private:private_stamp_detect"))

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
    file_deps = []  # list of Depsets needed by srcs
    add_label_list(ctx, content_map, file_deps, srcs = ctx.attr.srcs)
    file_inputs = depset(transitive = file_deps)

    manifest_file = ctx.actions.declare_file(ctx.label.name + ".manifest")
    inputs.append(manifest_file)
    write_manifest(ctx, manifest_file, content_map)
    args.add("--manifest", manifest_file.path)
    args.set_param_file_format("multiline")
    args.use_param_file("@%s")

    ctx.actions.run(
        mnemonic = "PackageZip",
        inputs = file_inputs.to_list() + inputs,
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
            file = output_file,
            file_name = output_name,
        ),
    ]

pkg_zip_impl = rule(
    implementation = _pkg_zip_impl,
    # @unsorted-dict-items
    attrs = {
        "srcs": attr.label_list(
            doc = """List of files that should be included in the archive.""",
            allow_files = True,
        ),
        "mode": attr.string(
            doc = """The default mode for all files in the archive.""",
            default = "0555",
        ),
        "package_dir": attr.string(
            doc = """The prefix to add to all all paths in the archive.""",
            default = "/",
        ),
        "strip_prefix": attr.string(),
        "timestamp": attr.int(
            doc = """Time stamp to place on all files in the archive, expressed
as seconds since the Unix Epoch, as per RFC 3339.  The default is January 01,
1980, 00:00 UTC.

Due to limitations in the format of zip files, values before
Jan 1, 1980 will be rounded up and the precision in the zip file is
limited to a granularity of 2 seconds.""",
            default = 315532800,
        ),

        # Common attributes
        "out": attr.output(
            doc = """output file name. Default: name + ".zip".""",
            mandatory = True,
        ),
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
        "_build_zip": attr.label(
            default = Label("//pkg/private/zip:build_zip"),
            cfg = "exec",
            executable = True,
            allow_files = True,
        ),
    },
    provides = [PackageArtifactInfo],
)

def pkg_zip(name, out = None, **kwargs):
    """Creates a .zip file.

    @wraps(pkg_zip_impl)

    Args:
      out: output file name. Default: name + ".zip".
    """
    if not out:
        out = name + ".zip"
    pkg_zip_impl(
        name = name,
        out = out,
        private_stamp_detect = select({
            _stamp_condition: True,
            "//conditions:default": False,
        }),
        **kwargs
    )
