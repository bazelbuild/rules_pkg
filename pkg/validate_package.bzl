# Copyright 2023 The Bazel Authors. All rights reserved.
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
"""Utility to test that an archive contains specific files."""

def _validate_archive_test_impl(ctx):
    args = ctx.actions.args()
    args.add("-archive", ctx.attr.target.path)

    args.add("-d", substitute_package_variables(ctx, ctx.attr.package_dir))
    args.add("-t", ctx.attr.timestamp)
    args.add("-m", ctx.attr.mode)
    inputs = []

    data_path = compute_data_path(ctx, ctx.attr.strip_prefix)
    data_path_without_prefix = compute_data_path(ctx, ".")

    content_map = {}  # content handled in the manifest
    file_deps = []  # list of Depsets needed by srcs
    add_label_list(ctx, content_map, file_deps, srcs = ctx.attr.srcs)

    manifest_file = ctx.actions.declare_file(ctx.label.name + ".manifest")
    inputs.append(manifest_file)
    write_manifest(ctx, manifest_file, content_map)
    args.add("--manifest", manifest_file.path)
    args.set_param_file_format("multiline")
    args.use_param_file("@%s")

    all_inputs = depset(direct = inputs, transitive = file_deps)

    ctx.actions.run(
        mnemonic = "PackageZip",
        inputs = all_inputs,
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
    ]



validate_archive_test = rule(
    implementation = _validate_archive_test_impl,
    test = True,
    # @unsorted-dict-items
    attrs = {
        "target": attr.label(
            doc = "Archive to test",
            allow_single_file = True,
        ),

        "contains": attr.string_list(
            doc = """List of path regexs that must be in the archive.""",
        ),
        "does_not_contain": attr.string_list(
            doc = """List of path regexs that must not be in the archive.""",
        ),
        "min_size": attr.int(
            doc = """Miniumn number of entries in the archive."""
        ),
        "max_size": attr.int(
            doc = """Miniumn number of entries in the archive."""
        ),

        # Implicit dependencies.
        "_validate_archive_test": attr.label(
            default = Label("//pkg/validate_archive_test"),
            cfg = "exec",
            executable = True,
            allow_files = True,
        ),
    },
)
