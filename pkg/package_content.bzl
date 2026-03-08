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
"""Utilities for collecting and serializing package content.

This module provides the building blocks for implementing custom packaging rules
on top of `rules_pkg`.  A typical custom rule implementation will:

1. Call `create_mapping_context_from_ctx` to set up a `MappingContext`.
2. Call `add_label_list` to resolve source labels into a content map.
3. Call `write_manifest` to serialize the content map as a JSON manifest.

Example usage in a custom rule implementation:

```starlark
load("@rules_pkg//pkg:package_content.bzl",
    "add_label_list",
    "create_mapping_context_from_ctx",
    "write_manifest",
)

def _my_packager_impl(ctx):
    mapping_context = create_mapping_context_from_ctx(ctx, ctx.label)
    add_label_list(mapping_context, ctx.attr.srcs)

    manifest = ctx.actions.declare_file(ctx.attr.name + "-manifest.json")
    write_manifest(ctx, manifest, mapping_context.content_map)
    ...
```
"""

load("//pkg:path.bzl", "compute_data_path")
load(
    "//pkg:providers.bzl",
    "PackageDirsInfo",
    "PackageFilegroupInfo",
    "PackageFilesInfo",
    "PackageSymlinkInfo",
)
load(
    "//pkg/private:pkg_files.bzl",
    "MappingContext",
    "add_from_default_info",
    "encode_manifest_entry",
    "process_pkg_dirs",
    "process_pkg_filegroup",
    "process_pkg_files",
    "process_pkg_symlink",
)

# buildifier: disable=function-docstring-args
def create_mapping_context_from_ctx(
        ctx,
        label,
        allow_duplicates_with_different_content = None,
        strip_prefix = None,
        include_runfiles = None,
        default_mode = None,
        path_mapper = None):
    """Construct a MappingContext.

    Args: See the provider definition.

    Returns:
        MappingContext
    """
    if allow_duplicates_with_different_content == None:
        allow_duplicates_with_different_content = ctx.attr.allow_duplicates_with_different_content if hasattr(ctx.attr, "allow_duplicates_with_different_content") else False
    if strip_prefix == None:
        strip_prefix = ctx.attr.strip_prefix if hasattr(ctx.attr, "strip_prefix") else ""
    if include_runfiles == None:
        include_runfiles = ctx.attr.include_runfiles if hasattr(ctx.attr, "include_runfiles") else False
    if default_mode == None:
        default_mode = ctx.attr.mode if hasattr(ctx.attr, "default_mode") else ""

    return MappingContext(
        content_map = dict(),
        file_deps_direct = list(),
        file_deps_transitive = list(),
        label = label,
        allow_duplicates_with_different_content = allow_duplicates_with_different_content,
        strip_prefix = strip_prefix,
        include_runfiles = include_runfiles,
        workspace_name = ctx.workspace_name,
        default_mode = default_mode,
        path_mapper = path_mapper or (lambda x: x),
        # TODO(aiuto): allow these to be passed in as needed. But, before doing
        # that, explore defauilt_uid/gid as 0 rather than None
        default_user = "",
        default_group = "",
        default_uid = None,
        default_gid = None,
    )

def process_src(mapping_context, src, origin):
    """Add an entry to the content map.

    Args:
      mapping_context: (r/w) a MappingContext
      src: Source Package*Info object
      origin: The rule instance adding this entry

    Returns:
      True if src was a Package*Info and added to content_map.
    """

    # Gather the files for every srcs entry here, even if it is not from
    # a pkg_* rule.
    if DefaultInfo in src:
        mapping_context.file_deps_transitive.append(src[DefaultInfo].files)
    found_info = False
    if PackageFilesInfo in src:
        process_pkg_files(
            mapping_context,
            src[PackageFilesInfo],
            origin,
        )
        found_info = True
    if PackageFilegroupInfo in src:
        process_pkg_filegroup(
            mapping_context,
            src[PackageFilegroupInfo],
        )
        found_info = True
    if PackageSymlinkInfo in src:
        process_pkg_symlink(
            mapping_context,
            src[PackageSymlinkInfo],
            origin,
        )
        found_info = True
    if PackageDirsInfo in src:
        process_pkg_dirs(
            mapping_context,
            src[PackageDirsInfo],
            origin,
        )
        found_info = True
    return found_info

def add_label_list(mapping_context, srcs):
    """Helper method to add a list of labels (typically 'srcs') to a content_map.

    Args:
      mapping_context: (r/w) a MappingContext
      srcs: List of source objects
    """

    # Compute the relative path
    data_path = compute_data_path(
        mapping_context.label,
        mapping_context.strip_prefix,
    )
    data_path_without_prefix = compute_data_path(
        mapping_context.label,
        ".",
    )

    for src in srcs:
        if not process_src(
            mapping_context,
            src = src,
            origin = src.label,
        ):
            # Add in the files of srcs which are not pkg_* types
            add_from_default_info(
                mapping_context,
                src,
                data_path,
                data_path_without_prefix,
                mapping_context.include_runfiles,
                mapping_context.workspace_name,
            )

def write_manifest(ctx, manifest_file, content_map, use_short_path = False, pretty_print = False):
    """Write a content map to a manifest file.

    The format of this file is currently undocumented, as it is a private
    contract between the rule implementation and the package writers.  It will
    become a published interface in a future release.

    For reproducibility, the manifest file must be ordered consistently.

    Args:
      ctx: rule context
      manifest_file: File object used as the output destination
      content_map: content_map (see concepts at top of file)
      use_short_path: write out the manifest file destinations in terms of "short" paths, suitable for `bazel run`.
      pretty_print: indent the output nicely. Takes more space so it is off by default.
    """
    ctx.actions.write(
        manifest_file,
        "[\n" + ",\n".join(
            [
                encode_manifest_entry(ctx, dst, content_map[dst], use_short_path, pretty_print)
                for dst in sorted(content_map.keys())
            ],
        ) + "\n]\n",
    )
