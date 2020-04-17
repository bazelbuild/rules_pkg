# Copyright 2020 The Bazel Authors. All rights reserved.
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

- `pkg_filegroup` describes destinations for rule outputs
- `pkg_mkdirs` describes directory structures

Rules that actually make use of the outputs of the above rules are not specified
here.  See `rpm.bzl` for an example that builds out RPM packages.
"""

load("@bazel_skylib//lib:paths.bzl", "paths")

_PKGFILEGROUP_STRIP_ALL = "."

####
# Provider interfaces
####

PackageFileInfo = provider(
    doc = """Groups a collection of files to be included in a package.

    This provider also includes certain metadata and dependency information.
    """,
    fields = {
        "srcs": "Source file list",
        "dests": "Destination file list",
        "attrs": "File attributes to be set on all 'dests' in this provider",
        "section": "'Section' property, see pkg_filegroup docs for details",
    },
)

PackageDirInfo = provider(
    doc = """Groups a collection of directories to be created within a package.

    Also owns directory attributes and other properties.
    """,
    fields = {
        "dirs": "Directories to be created within the package",
        "attrs": "File attributes to be set on all 'dirs' in this provider",
        "section": "'Section' property, see pkg_filegroup docs for details",
    },
)

####
# External-facing helpers
####

def make_strip_prefix(files_only = None, from_pkg = None, from_root = None):
    """Compute a strip_prefix value for a desired path stripping behavior.

    This function computes a value that can be used for the `pkg_filegroup`
    rule's `strip_prefix` attribute to select a desired path prefix stripping
    behavior.  Exactly one of `files_only`, `from_pkg`, and `from_root` must be
    set.

    This routine is used to instruct `pkg_filegroup` to remove (strip) path
    components from the file as it exists in the current repository.  After this
    is done, what's left of the path will be concatenated with the prefix as
    provided to `pkg_filegroup`.

    For arguments that accept paths (`from_pkg`, `from_root`), provided path
    components will only be stripped from files to be included in a
    `pkg_filegroup` if the `pkg_filegroup` paths contain all of the path
    components provided.  For example, if you have a root-relative file at:

    ```
    foo/srcs/prog
    ```

    And if you provide `from_root="foo/src"`, the path in the
    package will be:

    ```
    $PREFIX/foo/srcs/prog
    ```

    where $PREFIX is the `prefix` defined in the `pkg_filegroup`.  If
    `from_root="foo/srcs"`, then:

    ```
    $PREFIX/prog
    ```

    Args:
      files_only: Set to `True` or `False`.  If `True`, the paths will be stripped
        of all directories, leaving only the basename.

      from_pkg: Set to a path (string).  If provided, the entirety of the path
        leading up to the package name in which the files are found will be
        removed, followed by whatever is provided to this argument.  May be an
        empty string to strip all components through the package only.

      from_root: Set to a path (string).  If provided, path components to be
        removed will be considered relative to the workspace root where files in
        question are actually located.  May be an empty string to do no local
        path stripping.

    Returns:
      A path specification used by the `pkg_filegroup` implementation that
      instructs it to do path stripping as documented here.
    """

    # Exactly one must be "true"
    not_none_cnt = 0
    for b in [files_only, from_pkg, from_root]:
        if b != None:
            not_none_cnt += 1
    if not_none_cnt != 1:
        fail("Provide exactly one of files_only, from_pkg, or from_root")

    if files_only:  # Boolean, must be true
        return _PKGFILEGROUP_STRIP_ALL
    elif from_pkg != None:  # String, can be empty
        if from_pkg.startswith("/"):
            return from_pkg[1:]
        else:
            return from_pkg
    elif from_root != None:  # String, can be empty
        # Assume that the user has given us everything we need (accurately, too)
        if from_root.startswith("/"):
            return from_root
        else:
            return "/" + from_root
    else:
        # FIXME: We should probably migrate the files_only checks to the top of
        # the function, or make this into a struct-module so that this and the
        # other Noneness tests are obviated.
        #
        # The big thing this will catch is if files_only is "false"
        fail("Invalid make_strip_prefix arguments: files_only={}, from_pkg={}, from_root={}".format(
            files_only,
            from_pkg,
            from_root,
        ))

####
# Internal helpers
####

def _validate_attr(attr):
    # If/when the "attr" list expands, this should probably be modified to use
    # sets (like the one in skylib) instead
    valid_keys = ["unix"]
    for k in attr.keys():
        if k not in valid_keys:
            fail("Invalid attr {}, allowed are {}".format(k, valid_keys), "attrs")

    # We could do more here, perhaps
    if "unix" in attr.keys():
        if len(attr["unix"]) != 3:
            fail("'unix' attrs key must have three child values")

def _do_strip_prefix(path, to_strip):
    path_norm = paths.normalize(path)
    to_strip_norm = paths.normalize(to_strip) + "/"

    if path_norm.startswith(to_strip_norm):
        return path_norm[len(to_strip_norm):]
    else:
        return path_norm

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
    # XXX: Make this not a hack
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

####
# Rule/Macro implementations
####

def _pkg_filegroup_impl(ctx):
    # The input sources are already known.  Let's calculate the destinations...

    # Exclude excludes
    srcs = [f for f in ctx.files.srcs if f not in ctx.files.excludes]

    if ctx.attr.strip_prefix == _PKGFILEGROUP_STRIP_ALL:
        dests = [paths.join(ctx.attr.prefix, src.basename) for src in srcs]
    elif ctx.attr.strip_prefix.startswith("/"):
        # Relative to workspace/repository root
        dests = [
            paths.join(
                ctx.attr.prefix,
                _do_strip_prefix(
                    _path_relative_to_repo_root(f),
                    ctx.attr.strip_prefix[1:],
                ),
            )
            for f in srcs
        ]
    else:
        # Relative to package
        dests = [
            paths.join(
                ctx.attr.prefix,
                _do_strip_prefix(
                    _path_relative_to_package(f),
                    ctx.attr.strip_prefix,
                ),
            )
            for f in srcs
        ]

    # If the lengths of these are not the same, then it impossible to correlate
    # them in the actual package helpers, and in the map below.
    if len(srcs) != len(dests):
        fail("INTERNAL ERROR: pkg_filegroup length mismatch")

    # Dictionary for convenience purposes.
    #
    # TODO(nacl): It would be nice to be able to
    # build it in one fell swoop.
    src_dest_files_map = dict(zip(srcs, dests))

    _validate_attr(ctx.attr.attrs)

    # TODO(nacl): consider writing out a tiny parser for this
    valid_sections = [
        "",
        "doc",
        "config",
        "config(missingok)",
        "config(noreplace)",
        "config(missingok, noreplace)",
    ]

    if ctx.attr.section not in valid_sections:
        fail("Invalid 'section' value", "section")

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
        if src_file not in src_dest_files_map:
            fail(
                "File remapping from {0} to {1} is invalid: {0} is not provided to this rule or was excluded".format(rename_src, rename_dest),
                "renames",
            )
        src_dest_files_map[src_file] = paths.join(ctx.attr.prefix, rename_dest)

    return [
        PackageFileInfo(
            srcs = src_dest_files_map.keys(),
            dests = src_dest_files_map.values(),
            attrs = ctx.attr.attrs,
            section = ctx.attr.section,
        ),
        DefaultInfo(
            # Simple passthrough
            files = depset(src_dest_files_map.keys()),
        ),
    ]

pkg_filegroup = rule(
    doc = """General-purpose package target-to-destination mapping rule.

    This rule provides a specification for the locations and attributes of
    targets when they are packaged. No outputs are created other than Providers
    that are intended to be consumed by other packaging rules, such as
    `pkg_rpm`.

    Instead of providing the actual rules that generate your desired outputs to
    packaging rules, you instead pass in the associated `pkg_filegroup`.

    Consumers of `pkg_filegroup`s will, where possible, create the necessary
    directory structure for your files so you do not have to unless you have
    special requirements.  Consult `pkg_mkdirs` for more details.
    """,
    implementation = _pkg_filegroup_impl,
    # @unsorted-dict-items
    attrs = {
        "srcs": attr.label_list(
            doc = """Files/Labels to include in this target filegroup""",
            mandatory = True,
            allow_files = True,
        ),
        "attrs": attr.string_list_dict(
            doc = """Attributes to set for the output targets

            Must be a dict of:

            ```
            "unix" : [
                "Four-digit octal permissions string (e.g. "0644") or "-" (don't change from what's provided),
                "User Id, or "-" (use current user)",
                "Group Id, or "-" (use current group)",
            ]
            ```

            All values default to "-".
            """,
            default = {"unix": ["-", "-", "-"]},
        ),
        "prefix": attr.string(
            doc = """Installation prefix.

            This may be an arbitrary string, but it should be understandable by
            the packaging system you are using to have the desired outcome.  For
            example, RPM macros like `%{_libdir}` may work correctly in paths
            for RPM packages, not, say, Debian packages.

            """,
            default = "",
        ),
        "section": attr.string(
            doc = """Type of file this pkg_filegroup gathers for installation.
            Legal values for section are:
            - "" (i.e. an empty string)
            - "doc"
            - "config"
            - "config(missingok)"
            - "config(noreplace)"
            - "config(missingok, noreplace)"

            "doc" specifies the file is documentation, and "config" specifies
            the file is a configuration file. The section attribute should be
            omitted or an empty string should be explicitly passed for any other
            kind of file. Note some package managers (for example, RPM) may
            treat documentation and configuration files differently than other
            installable files.

            Some package managers (such as RPM) may also recognize the
            "missingok" and/or "noreplace" sub-types of configuration files
            (which are not mutually exclusive). "missingok" directs the package
            manager not to report an error if the file is missing when
            validating an installation of the package. "noreplace" tells the
            package manager not to overwrite or move an existing configuration
            file when upgrading an installation (the package manager should
            instead move where it places the new version of the configuration
            file).

            If a legal value (enumerated above) is given for the section
            attribute but a a package is built for a type of package manager
            that does not support that given value, that section value will
            simply be ignored. If "config" was given with a sub-type (i.e.
            "missingok" or "no-replace"), the value of section may be treated as
            if it were just "config" if a package is built for a package manager
            that distinguishes configuration files but does not recognize these
            sub-types.
            """,
            default = "",
        ),
        "strip_prefix": attr.string(
            doc = """What prefix of a file's path to discard prior to installation.

            This specifies what prefix of an incoming file's path should not be
            included in the path the file is installed at after being appended
            to the install prefix (the prefix attribute).  Note that this is
            only applied to full directory names, see `make_strip_prefix` for
            more details.

            Use the `make_strip_prefix()` function to define this attribute.  If this
            attribute is not specified, all directories will be stripped from
            all files prior to being included in packages
            (`make_strip_prefix(files_only = True`).
            """,
            default = make_strip_prefix(files_only = True),
        ),
        "excludes": attr.label_list(
            doc = """List of files or labels to exclude from the inputs to this pkg_filegroup.

            Mostly useful for removing files from generated outputs or
            preexisting `filegroup`s.
            """,
            allow_files = True,
            default = [],
        ),
        "renames": attr.label_keyed_string_dict(
            doc = """Destination override map

            This attribute allows the user to override destinations of files in
            `pkg_filegroup`s relative to the `prefix` attribute.  Keys to the
            dict are source files/labels, values are destinations relative to
            the `prefix`, ignoring whatever value was provided for
            `strip_prefix`.

            This is the most effective way to rename files using
            `pkg_filegroup`s.  For single files, consider using
            `pkg_rename_single`.

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
)

def pkg_rename_single(name = None, src = None, dest = None, **kwargs):
    """Macro that eases the renaming of files in `pkg_filegroup`s

    Effectively calls:

    ```
    pkg_filegroup(
        name = name,
        deps = [src],
        renames = {src : dest},
        **kwargs,
    )
    ```

    All of `name`, `src`, and `dest` must be provided.

    Args:
      name: (String) Name of the underlying `pkg_filegroup`.

      src: (String/Label) Source file/label to copy from.  Must refer to exactly one
        file/output (see `renames` in `pkg_filegroup`).

      dest: (String) Destination within packages.

      **kwargs: Additional args to be passed `pkg_filegroup`.  Useful ones
        include `attrs` and `section`; see the relevant documentation in
        `pkg_filegroup`.
    """
    if None in [name, src, dest]:
        fail("All of 'name', 'src', and 'dest' must be provided")

    rule_args = kwargs

    rule_args["name"] = name
    rule_args["srcs"] = [src]
    rule_args["renames"] = {src: dest}

    pkg_filegroup(**rule_args)

def _pkg_mkdirs_impl(ctx):
    _validate_attr(ctx.attr.attrs)

    if ctx.attr.section not in ["dir", "docdir"]:
        fail("Invalid 'section' value", "section")
    return [
        PackageDirInfo(
            dirs = ctx.attr.dirs,
            attrs = ctx.attr.attrs,
            section = ctx.attr.section,
        ),
    ]

pkg_mkdirs = rule(
    doc = """pkg_filegroup-like rule for the creation and ownership of directories.

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
            doc = """Directory names to make within the package""",
            mandatory = True,
        ),
        "attrs": attr.string_list_dict(
            doc = """Attributes to set for the output targets.

            Must be a dict of:

            ```
            "unix" : [
                "Four-digit octal permissions string (e.g. "0755") or "-" (don't change from what's provided),
                "User Id, or "-" (use current user)",
                "Group Id, or "-" (use current group)",
            ]
            ```

            All values default to "-".
            """,
            default = {"unix": ["-", "-", "-"]},
        ),
        "section": attr.string(
            doc = """Directory type used by package generators.

            Legal values are:

            - `dir`
            - `docdir`

            `dir` specifies that the provided paths will just be plain old
            directories without any special characteristics.

            `docdir` is like `dir` but also specifies that this directory will
            exclusively contain documentation.

            The default is `dir`.
            """,
            default = "dir",
        ),
    },
)
