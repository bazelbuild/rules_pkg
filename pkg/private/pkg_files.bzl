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
"""Internal functions for processing pkg_file* instances.

Concepts and terms:

  DestFile: A provider holding the source path, attributes and other
            information about a file that should appear in the package.
            When attributes are empty in DestFile, we let the package
            tool decide their values.

  content map: The map of destination paths to DestFile instances. Note that
               several distinct destinations make share the same source path.
               Attempting to insert a duplicate entry in the content map is
               an error, because it means you are collapsing files together.
               We may want to relax this in the future if their DestFiles
               are equal.

  manifest: The file which represents the content map. This is generated
            by rule implementations and passed to the build_*.py helpers.
"""

load("//pkg:path.bzl", "compute_data_path", "dest_path")
load(
    "//pkg:providers.bzl",
    "PackageArtifactInfo",
    "PackageDirsInfo",
    "PackageFilegroupInfo",
    "PackageFilesInfo",
    "PackageSymlinkInfo",
)

ENTRY_IS_FILE = "file"  # Entry is a file: take content from <src>
ENTRY_IS_LINK = "symlink"  # Entry is a symlink: dest -> <src>
ENTRY_IS_DIR = "dir"  # Entry is an empty dir
ENTRY_IS_TREE = "tree" # Entry is a tree artifact: take tree from <src>
ENTRY_IS_EMPTY_FILE = "empty-file"  # Entry is a an empty file

_DestFile = provider(
    doc = """Information about each destination in the final package.""",
    fields = {
        "src": "source file",
        "mode": "mode, or empty",
        "user": "user, or empty",
        "group": "group, or empty",
        "link_to": "path to link to. src must not be set",
        "entry_type": "string.  See ENTRY_IS_* values above.",
        "origin": "target which added this",
    },
)

def _check_dest(content_map, dest, src, origin):
    old_entry = content_map.get(dest)
    if not old_entry:
        return
    if old_entry.src == src or old_entry.origin == origin:
        return

    # TODO(#385): This is insufficient but good enough for now. We should
    # compare over all the attributes too. That will detect problems where
    # people specify the owner in one place, but another overly broad glob
    # brings in the file with a different owner.
    if old_entry.src.path != src.path:
        # buildifier: disable=print
        print(
            "Duplicate output path: <%s>, declared in %s and %s" % (
                dest,
                origin,
                content_map[dest].origin,
            ),
            "\n  SRC:",
            src,
        )

def _merge_attributes(info, mode, user, group):
    if hasattr(info, "attributes"):
        attrs = info.attributes
        mode = attrs.get("mode") or mode
        user = attrs.get("user") or user
        group = attrs.get("group") or group
    return (mode, user, group)

def _process_pkg_dirs(content_map, pkg_dirs_info, origin, default_mode, default_user, default_group):
    attrs = _merge_attributes(pkg_dirs_info, default_mode, default_user, default_group)
    for dir in pkg_dirs_info.dirs:
        dest = dir.strip("/")
        _check_dest(content_map, dest, None, origin)
        content_map[dest] = _DestFile(
            src = None,
            entry_type = ENTRY_IS_DIR,
            mode = attrs[0],
            user = attrs[1],
            group = attrs[2],
            origin = origin,
        )

def _process_pkg_files(content_map, pkg_files_info, origin, default_mode, default_user, default_group):
    attrs = _merge_attributes(pkg_files_info, default_mode, default_user, default_group)
    for filename, src in pkg_files_info.dest_src_map.items():
        dest = filename.strip("/")
        _check_dest(content_map, dest, src, origin)
        content_map[dest] = _DestFile(
            src = src,
            entry_type = ENTRY_IS_TREE if src.is_directory else ENTRY_IS_FILE,
            mode = attrs[0],
            user = attrs[1],
            group = attrs[2],
            origin = origin,
        )

def _process_pkg_symlink(content_map, pkg_symlink_info, origin, default_mode, default_user, default_group):
    dest = pkg_symlink_info.destination.strip("/")
    attrs = _merge_attributes(pkg_symlink_info, default_mode, default_user, default_group)
    _check_dest(content_map, dest, None, origin)
    content_map[dest] = _DestFile(
        src = None,
        entry_type = ENTRY_IS_LINK,
        mode = attrs[0],
        user = attrs[1],
        group = attrs[2],
        origin = origin,
        link_to = pkg_symlink_info.target,
    )

def _process_pkg_filegroup(content_map, pkg_filegroup_info, origin, default_mode, default_user, default_group):
    if hasattr(pkg_filegroup_info, "pkg_dirs"):
        for d in pkg_filegroup_info.pkg_dirs:
            _process_pkg_dirs(content_map, d[0], d[1], default_mode, default_user, default_group)
    if hasattr(pkg_filegroup_info, "pkg_files"):
        for pf in pkg_filegroup_info.pkg_files:
            _process_pkg_files(content_map, pf[0], pf[1], default_mode, default_user, default_group)
    if hasattr(pkg_filegroup_info, "pkg_symlinks"):
        for psl in pkg_filegroup_info.pkg_symlinks:
            _process_pkg_symlink(content_map, psl[0], psl[1], default_mode, default_user, default_group)

def process_src(
        content_map,
        files,
        src,
        origin,
        default_mode,
        default_user,
        default_group):
    """Add an entry to the content map.

    Args:
      content_map: in/out The content map
      files: in/out list of file Depsets represented in the map
      src: Source Package*Info object
      origin: The rule instance adding this entry
      default_mode: fallback mode to use for Package*Info elements without mode
      default_user: fallback user to use for Package*Info elements without user
      default_group: fallback mode to use for Package*Info elements without group

    Returns:
      True if src was a Package*Info and added to content_map.
    """

    # Gather the files for every srcs entry here, even if it is not from
    # a pkg_* rule.
    if DefaultInfo in src:
        files.append(src[DefaultInfo].files)
    found_info = False
    if PackageFilesInfo in src:
        _process_pkg_files(
            content_map,
            src[PackageFilesInfo],
            origin,
            default_mode = default_mode,
            default_user = default_user,
            default_group = default_group,
        )
        found_info = True
    if PackageFilegroupInfo in src:
        _process_pkg_filegroup(
            content_map,
            src[PackageFilegroupInfo],
            origin,
            default_mode = default_mode,
            default_user = default_user,
            default_group = default_group,
        )
        found_info = True
    if PackageSymlinkInfo in src:
        _process_pkg_symlink(
            content_map,
            src[PackageSymlinkInfo],
            origin,
            default_mode = default_mode,
            default_user = default_user,
            default_group = default_group,
        )
        found_info = True
    if PackageDirsInfo in src:
        _process_pkg_dirs(
            content_map,
            src[PackageDirsInfo],
            origin,
            default_mode = "0555",
            default_user = default_user,
            default_group = default_group,
        )
        found_info = True
    return found_info

def add_directory(content_map, dir_path, origin, mode = None, user = None, group = None):
    """Add an empty directory to the content map.

    Args:
      content_map: The content map
      dir_path: Where to place the file in the package.
      origin: The rule instance adding this entry
      mode: fallback mode to use for Package*Info elements without mode
      user: fallback user to use for Package*Info elements without user
      group: fallback mode to use for Package*Info elements without group
    """
    content_map[dir_path.strip("/")] = _DestFile(
        src = None,
        entry_type = ENTRY_IS_DIR,
        origin = origin,
        mode = mode,
        user = user,
        group = group,
    )

def add_empty_file(content_map, dest_path, origin, mode = None, user = None, group = None):
    """Add a single file to the content map.

    Args:
      content_map: The content map
      dest_path: Where to place the file in the package.
      origin: The rule instance adding this entry
      mode: fallback mode to use for Package*Info elements without mode
      user: fallback user to use for Package*Info elements without user
      group: fallback mode to use for Package*Info elements without group
    """
    dest = dest_path.strip("/")
    _check_dest(content_map, dest, None, origin)
    content_map[dest] = _DestFile(
        src = None,
        entry_type = ENTRY_IS_EMPTY_FILE,
        origin = origin,
        mode = mode,
        user = user,
        group = group,
    )

def add_label_list(
        ctx,
        content_map,
        file_deps,
        srcs,
        default_mode = None,
        default_user = None,
        default_group = None):
    """Helper method to add a list of labels (typically 'srcs') to a content_map.

    Args:
      ctx: rule context.
      content_map: (r/w) The content map to update.
      file_deps: (r/w) The list of file Depsets that srcs depend on.
      srcs: List of source objects.
      default_mode: fallback mode to use for Package*Info elements without mode
      default_user: fallback user to use for Package*Info elements without user
      default_group: fallback mode to use for Package*Info elements without group
    """

    if hasattr(ctx.attr, "include_runfiles"):
        include_runfiles = ctx.attr.include_runfiles
    else:
        include_runfiles = False

    # Compute the relative path
    data_path = compute_data_path(
        ctx,
        ctx.attr.strip_prefix if hasattr(ctx.attr, "strip_prefix") else "",
    )
    data_path_without_prefix = compute_data_path(ctx, ".")

    for src in srcs:
        if not process_src(
            content_map,
            file_deps,
            src = src,
            origin = src.label,
            default_mode = default_mode,
            default_user = default_user,
            default_group = default_group,
        ):
            # Add in the files of srcs which are not pkg_* types
            add_from_default_info(
                content_map,
                file_deps,
                src,
                data_path,
                data_path_without_prefix,
                default_mode = default_mode,
                default_user = default_user,
                default_group = default_group,
                include_runfiles = include_runfiles,
            )

def add_from_default_info(
        content_map,
        file_deps,
        src,
        data_path,
        data_path_without_prefix,
        default_mode = None,
        default_user = None,
        default_group = None,
        include_runfiles = False):
    """Helper method to add the DefaultInfo of a target to a content_map.

    Args:
      content_map: (r/w) The content map to update.
      file_deps: (r/w) The list of file Depsets that srcs depend on.
      src: A source object.
      data_path: path to package
      data_path_without_prefix: path to the package after prefix stripping
      default_mode: fallback mode to use for Package*Info elements without mode
      default_user: fallback user to use for Package*Info elements without user
      default_group: fallback mode to use for Package*Info elements without group
      include_runfiles: Include runfiles
    """
    if not DefaultInfo in src:
        return

    # Auto-detect the executable so we can set its mode.
    the_executable = get_my_executable(src)
    all_files = src[DefaultInfo].files.to_list()
    for f in all_files:
        d_path = dest_path(f, data_path, data_path_without_prefix)
        if f.is_directory:
            add_tree_artifact(
                content_map,
                d_path,
                f,
                origin = src.label,
                mode = default_mode,
                user = default_user,
                group = default_group,
            )
        else:
            fmode = "0755" if f == the_executable else default_mode
            add_single_file(
                content_map,
                dest_path = d_path,
                src = f,
                origin = src.label,
                mode = fmode,
                user = default_user,
                group = default_group,
            )
    if include_runfiles:
        runfiles = src[DefaultInfo].default_runfiles
        if runfiles:
            base_path = d_path + ".runfiles"
            for rf in runfiles.files.to_list():
                d_path = base_path + "/" + rf.short_path
                fmode = "0755" if rf == the_executable else default_mode
                _check_dest(content_map, d_path, rf, src.label)
                content_map[d_path] = _DestFile(
                    src = rf,
                    entry_type = ENTRY_IS_FILE,
                    origin = src.label,
                    mode = fmode,
                    user = default_user,
                    group = default_group,
                )

def get_my_executable(src):
    """If a target represents an executable, return its file handle.

    The roundabout hackery here is because there is no good way to see if
    DefaultInfo was created with an executable in it.
    See: https://github.com/bazelbuild/bazel/issues/14811

    Args:
      src: A label.
    Returns:
      File or None.
    """
    if not DefaultInfo in src:
        return None
    di = src[DefaultInfo]
    if not hasattr(di, "files_to_run"):
        return None
    ftr = di.files_to_run

    # The docs lead you to believe that you could look at
    # files_to_run.executable, but that is filled out even for source
    # files.
    if not hasattr(ftr, "runfiles_manifest"):
        return None
    if ftr.runfiles_manifest:
        # DEBUG print("Got an manifest executable", ftr.executable)
        return ftr.executable
    return None

def add_single_file(content_map, dest_path, src, origin, mode = None, user = None, group = None):
    """Add an single file to the content map.

    Args:
      content_map: The content map
      dest_path: Where to place the file in the package.
      src: Source object. Must have len(src[DefaultInfo].files) == 1
      origin: The rule instance adding this entry
      mode: fallback mode to use for Package*Info elements without mode
      user: fallback user to use for Package*Info elements without user
      group: fallback mode to use for Package*Info elements without group
    """
    dest = dest_path.strip("/")
    _check_dest(content_map, dest, src, origin)
    content_map[dest] = _DestFile(
        src = src,
        entry_type = ENTRY_IS_FILE,
        origin = origin,
        mode = mode,
        user = user,
        group = group,
    )

def add_symlink(content_map, dest_path, src, origin, mode = None, user = None, group = None):
    """Add a symlink to the content map.

    Args:
      content_map: The content map
      dest_path: Where to place the file in the package.
      src: Path to link to.
      origin: The rule instance adding this entry
      mode: fallback mode to use for Package*Info elements without mode
      user: fallback user to use for Package*Info elements without user
      group: fallback mode to use for Package*Info elements without group
    """
    dest = dest_path.strip("/")
    _check_dest(content_map, dest, None, origin)
    content_map[dest] = _DestFile(
        src = None,
        link_to = src,
        entry_type = ENTRY_IS_LINK,
        origin = origin,
        mode = mode,
        user = user,
        group = group,
    )

def add_tree_artifact(content_map, dest_path, src, origin, mode = None, user = None, group = None):
    """Add an tree artifact (directory output) to the content map.

    Args:
      content_map: The content map
      dest_path: Where to place the file in the package.
      src: Source object. Must have len(src[DefaultInfo].files) == 1
      origin: The rule instance adding this entry
      mode: fallback mode to use for Package*Info elements without mode
      user: fallback user to use for Package*Info elements without user
      group: fallback mode to use for Package*Info elements without group
    """
    content_map[dest_path] = _DestFile(
        src = src,
        origin = origin,
        entry_type = ENTRY_IS_TREE,
        mode = mode,
        user = user,
        group = group,
    )

def write_manifest(ctx, manifest_file, content_map, use_short_path=False, pretty_print=False):
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
    """
    ctx.actions.write(
        manifest_file,
        "[\n" + ",\n".join(
            [
                _encode_manifest_entry(dst, content_map[dst], use_short_path, pretty_print)
                for dst in sorted(content_map.keys())
            ]
        ) + "\n]\n"
    )

def _encode_manifest_entry(dest, df, use_short_path, pretty_print=False):
    entry_type = df.entry_type if hasattr(df, "entry_type") else ENTRY_IS_FILE
    if df.src:
        src = df.src.short_path if use_short_path else df.src.path
        # entry_type is left as-is

    elif hasattr(df, "link_to"):
        src = df.link_to
        entry_type = ENTRY_IS_LINK
    else:
        src = None

    # Bazel 6 has a new flag "--incompatible_unambiguous_label_stringification"
    # (https://github.com/bazelbuild/bazel/issues/15916) that causes labels in
    # the repository in which Bazel was run to be stringified with a preceding
    # "@".  In older versions, this flag did not exist.
    #
    # Since this causes all sorts of chaos with our tests, be consistent across
    # all Bazel versions.
    origin_str = str(df.origin)
    if not origin_str.startswith('@'):
        origin_str = '@' + origin_str

    data = {
        "type": df.entry_type,
        "src": src,
        "dest": dest.strip("/"),
        "mode": df.mode or "",
        "user": df.user or None,
        "group": df.group or None,
        "origin": origin_str,
    }

    if pretty_print:
        return json.encode_indent(data)
    else:
        return json.encode(data)
