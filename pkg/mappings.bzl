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

"""Package creation helper mapping rules.

This module declares Provider interfaces and rules for specifying the contents
of packages in a package-type-agnostic way.  The main rules supported here are
the following:

- `pkg_files` describes destinations for rule outputs
- `pkg_mkdirs` describes directory structures

Rules that actually make use of the outputs of the above rules are not specified
here.  TODO(nacl): implement one.
"""

load("@bazel_skylib//lib:paths.bzl", "paths")
load("//:providers.bzl", "PackageDirsInfo", "PackageFilesInfo")

_PKGFILEGROUP_STRIP_ALL = "."

def _sp_files_only():
    return _PKGFILEGROUP_STRIP_ALL

def _sp_from_pkg(path = ""):
    if path.startswith("/"):
        return path[1:]
    else:
        return path

def _sp_from_root(path = ""):
    if path.startswith("/"):
        return path
    else:
        return "/" + path

strip_prefix = struct(
    _doc = """pkg_files `strip_prefix` helper.  Instructs `pkg_files` what to do with directory prefixes of files.

    Each member is a function that equates to:

    - `files_only()`: strip all directory components from all paths

    - `from_pkg(path)`: strip all directory components up to the current
      package, plus what's in `path`, if provided.

    - `from_root(path)`: strip beginning from the file's WORKSPACE root (even if
      it is in an external workspace) plus what's in `path`, if provided.
    
    Prefix stripping is applied to each `src` in a `pkg_files` rule
    independently.
 """,
    files_only = _sp_files_only,
    from_pkg = _sp_from_pkg,
    from_root = _sp_from_root,
)

def pkg_attributes(mode = "0444", user = None, group = None, **kwargs):
    """Format attributes for use in package mapping rules.

    Args:
      mode: string: UNIXy octal permissions, as a string.  Defaults to being read-only ("0444")
      user: string: Filesystem owning user.
      group: string: Filesystem owning group.
      **kwargs: any other desired attributes.

    Not providing any of "user", or "group" will result in the package builder
    choosing one for you.  The chosen value should not be relied upon.

    Well-known attributes outside of the above are documented in the rules_pkg
    reference.

    This is the only supported means of passing in attributes to package mapping
    rules (e.g. `pkg_files`).

    Returns:
      A value usable in the "attributes" attribute in package mapping rules.

    """
    ret = kwargs
    ret["mode"] = mode
    if user:
        ret["user"] = user
    if group:
        ret["group"] = group
    return json.encode(ret)

####
# Internal helpers
####

def _do_strip_prefix(path, to_strip, src_file):
    if to_strip == "":
        # We were asked to strip nothing, which is valid.  Just return the
        # original path.
        return path

    path_norm = paths.normalize(path)
    to_strip_norm = paths.normalize(to_strip) + "/"

    if path_norm.startswith(to_strip_norm):
        return path_norm[len(to_strip_norm):]
    else:
        # Avoid user surprise by failing if prefix stripping doesn't work as
        # expected.
        #
        # We already leave enough breadcrumbs, so if File.owner() returns None,
        # this won't be a problem.
        fail("Could not strip prefix '{}' from file {} ({})".format(to_strip, str(src_file), str(src_file.owner)))

# The below routines make use of some path checking magic that may difficult to
# understand out of the box.  This following table may be helpful to demonstrate
# how some of these members may look like in real-world usage:
#
# Note: "F" is "File", "FO": is "File.owner".

# | File type | Repo     | `F.path`                                                 | `F.root.path`                | `F.short_path`          | `FO.workspace_name` | `FO.workspace_root` |
# |-----------|----------|----------------------------------------------------------|------------------------------|-------------------------|---------------------|---------------------|
# | Source    | Local    | `dirA/fooA`                                              |                              | `dirA/fooA`             |                     |                     |
# | Generated | Local    | `bazel-out/k8-fastbuild/bin/dirA/gen.out`                | `bazel-out/k8-fastbuild/bin` | `dirA/gen.out`          |                     |                     |
# | Source    | External | `external/repo2/dirA/fooA`                               |                              | `../repo2/dirA/fooA`    | `repo2`             | `external/repo2`    |
# | Generated | External | `bazel-out/k8-fastbuild/bin/external/repo2/dirA/gen.out` | `bazel-out/k8-fastbuild/bin` | `../repo2/dirA/gen.out` | `repo2`             | `external/repo2`    |

def _owner(file):
    # File.owner allows us to find a label associated with a file.  While highly
    # convenient, it may return None in certain circumstances, which seem to be
    # primarily when bazel doesn't know about the files in question.
    #
    # Given that a sizeable amount of the code we have here relies on it, we
    # should fail() when we encounter this if only to make the rare error more
    # clear.
    #
    # File.owner returns a Label structure
    if file.owner == None:
        fail("File {} ({}) has no owner attribute; cannot continue".format(file, file.path))
    else:
        return file.owner

def _relative_workspace_root(label):
    # Helper function that returns the workspace root relative to the bazel File
    # "short_path", so we can exclude external workspace names in the common
    # path stripping logic.
    #
    # This currently is "../$LABEL_WORKSPACE_ROOT" if the label has a specific
    # workspace name specified, else it's just an empty string.
    #
    # TODO(nacl): Make this not a hack
    return paths.join("..", label.workspace_name) if label.workspace_name else ""

def _path_relative_to_package(file):
    # Helper function that returns a path to a file relative to its package.
    owner = _owner(file)
    return paths.relativize(
        file.short_path,
        paths.join(_relative_workspace_root(owner), owner.package),
    )

def _path_relative_to_repo_root(file):
    # Helper function that returns a path to a file relative to its workspace root.
    return paths.relativize(
        file.short_path,
        _relative_workspace_root(_owner(file)),
    )

def _pkg_files_impl(ctx):
    # The input sources are already known.  Let's calculate the destinations...

    # Exclude excludes
    srcs = [f for f in ctx.files.srcs if f not in ctx.files.excludes]

    if ctx.attr.strip_prefix == _PKGFILEGROUP_STRIP_ALL:
        src_dest_paths_map = {src: paths.join(ctx.attr.prefix, src.basename) for src in srcs}
    elif ctx.attr.strip_prefix.startswith("/"):
        # Relative to workspace/repository root
        src_dest_paths_map = {src: paths.join(
            ctx.attr.prefix,
            _do_strip_prefix(
                _path_relative_to_repo_root(src),
                ctx.attr.strip_prefix[1:],
                src,
            ),
        ) for src in srcs}
    else:
        # Relative to package
        src_dest_paths_map = {src: paths.join(
            ctx.attr.prefix,
            _do_strip_prefix(
                _path_relative_to_package(src),
                ctx.attr.strip_prefix,
                src,
            ),
        ) for src in srcs}

    out_attributes = json.decode(ctx.attr.attributes)

    # Do file renaming
    for rename_src, rename_dest in ctx.attr.renames.items():
        # rename_src.files is a depset
        rename_src_files = rename_src.files.to_list()

        # Need to do a length check before proceeding.  We cannot rename
        # multiple files simultaneously.
        if len(rename_src_files) != 1:
            fail(
                "Target {} expands to multiple files, should only refer to one".format(rename_src),
                "renames",
            )

        src_file = rename_src_files[0]
        if src_file not in src_dest_paths_map:
            fail(
                "File remapping from {0} to {1} is invalid: {0} is not provided to this rule or was excluded".format(rename_src, rename_dest),
                "renames",
            )
        src_dest_paths_map[src_file] = paths.join(ctx.attr.prefix, rename_dest)

    # At this point, we have a fully valid src -> dest mapping in src_dest_paths_map.
    #
    # Construct the inverse of this mapping to pass to the output providers, and
    # check for duplicated destinations.
    dest_src_map = {}
    for src, dest in src_dest_paths_map.items():
        if dest in dest_src_map:
            fail("After renames, multiple sources (at least {0}, {1}) map to the same destination.  Consider adjusting strip_prefix and/or renames".format(dest_src_map[dest].path, src.path))
        dest_src_map[dest] = src

    return [
        PackageFilesInfo(
            dest_src_map = dest_src_map,
            attributes = out_attributes,
        ),
        DefaultInfo(
            # Simple passthrough
            files = depset(dest_src_map.values()),
        ),
    ]

pkg_files = rule(
    doc = """General-purpose package target-to-destination mapping rule.

    This rule provides a specification for the locations and attributes of
    targets when they are packaged. No outputs are created other than Providers
    that are intended to be consumed by other packaging rules, such as
    `pkg_rpm`.
    
    Labels associated with these rules are not passed directly to packaging
    rules, instead, they should be passed to an associated `pkg_filegroup` rule,
    which in turn should be passed to packaging rules.

    Consumers of `pkg_files`s will, where possible, create the necessary
    directory structure for your files so you do not have to unless you have
    special requirements.  Consult `pkg_mkdirs` for more details.
    """,
    implementation = _pkg_files_impl,
    # @unsorted-dict-items
    attrs = {
        "srcs": attr.label_list(
            doc = """Files/Labels to include in the outputs of these rules""",
            mandatory = True,
            allow_files = True,
        ),
        "attributes": attr.string(
            doc = """Attributes to set on packaged files.

            Always use `pkg_attributes()` to set this rule attribute.

            Consult the "Mapping Attributes" documentation in the rules_pkg
            reference for more details.
            """,
            default = pkg_attributes(),
        ),
        "prefix": attr.string(
            doc = """Installation prefix.

            This may be an arbitrary string, but it should be understandable by
            the packaging system you are using to have the desired outcome.  For
            example, RPM macros like `%{_libdir}` may work correctly in paths
            for RPM packages, not, say, Debian packages.

            If any part of the directory structure of the computed destination
            of a file provided to `pkg_filegroup` or any similar rule does not
            already exist within a package, the package builder will create it
            for you with a reasonable set of default permissions (typically
            `0755 root.root`).

            It is possible to establish directory structures with arbitrary
            permissions using `pkg_mkdirs`.
            """,
            default = "",
        ),
        "strip_prefix": attr.string(
            doc = """What prefix of a file's path to discard prior to installation.

            This specifies what prefix of an incoming file's path should not be
            included in the output package at after being appended to the
            install prefix (the `prefix` attribute).  Note that this is only
            applied to full directory names, see `strip_prefix` for more
            details.

            Use the `strip_prefix` struct to define this attribute.  If this
            attribute is not specified, all directories will be stripped from
            all files prior to being included in packages
            (`strip_prefix.files_only()`).
            
            If prefix stripping fails on any file provided in `srcs`, the build
            will fail.
            
            Note that this only functions on paths that are known at analysis
            time.  Specifically, this will not consider directories within
            TreeArtifacts (directory outputs), or the directories themselves.
            See also #269.
            """,
            default = strip_prefix.files_only(),
        ),
        "excludes": attr.label_list(
            doc = """List of files or labels to exclude from the inputs to this rule.

            Mostly useful for removing files from generated outputs or
            preexisting `filegroup`s.
            """,
            default = [],
            allow_files = True,
        ),
        "renames": attr.label_keyed_string_dict(
            doc = """Destination override map.

            This attribute allows the user to override destinations of files in
            `pkg_file`s relative to the `prefix` attribute.  Keys to the
            dict are source files/labels, values are destinations relative to
            the `prefix`, ignoring whatever value was provided for
            `strip_prefix`.

            The following keys are rejected:

            - Any label that expands to more than one file (mappings must be
              one-to-one).

            - Any label or file that was either not provided or explicitly
              `exclude`d.
            """,
            default = {},
            allow_files = True,
        ),
    },
    provides = [PackageFilesInfo],
)

def _pkg_mkdirs_impl(ctx):
    return [
        PackageDirsInfo(
            dirs = ctx.attr.dirs,
            attributes = json.decode(ctx.attr.attributes),
        ),
    ]

pkg_mkdirs = rule(
    doc = """Defines creation and ownership of directories in packages

    Use this if:

    1) You need to create an empty directory in your package.

    2) Your package needs to explicitly own a directory, even if it already owns
       files in those directories.

    3) You need nonstandard permissions (typically, not "0755") on a directory
       in your package.

    For some package management systems (e.g. RPM), directory ownership (2) may
    imply additional semantics.  Consult your package manager's and target
    distribution's documentation for more details.
    """,
    implementation = _pkg_mkdirs_impl,
    # @unsorted-dict-items
    attrs = {
        "dirs": attr.string_list(
            doc = """Directory names to make within the package

            If any part of the requested directory structure does not already
            exist within a package, the package builder will create it for you
            with a reasonable set of default permissions (typically `0755
            root.root`).

            """,
            mandatory = True,
        ),
        "attributes": attr.string(
            doc = """Attributes to set on packaged directories.

            Always use `pkg_attributes()` to set this rule attribute.

            The default value for this is UNIX "0755", or the target
            platform's equivalent.  All other values are left unspecified.

            Consult the "Mapping Attributes" documentation in the rules_pkg
            reference for more details.
            """,
            default = pkg_attributes(mode = "0755"),
        ),
    },
    provides = [PackageDirsInfo],
)
