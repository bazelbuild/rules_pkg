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

# NOTE: this is conceptutal and is intended as a discussion starter.  It may be
# the basis for further implementation.  It may be unusable as it currently
# stands.

"""
THOERY:

Files are often packaged in a hierarchical manner, so users should be able to
model such hierarchies in their BUILD files.

The previous implementation was highly rule-oriented, and required users to list
out every single file grouping in a clumsy manner.

IMPLEMENTATION:

This mockup provides a `pkg_file` macro, which defines a `_pkg_file` rule, which
associates inputs with their filesystem properties.  The macro is intended to be
provided directly into `pkg_filegroup` rules.

The `pkg_filegroup` rule provides a way to collect `pkg_file` inputs and
associate them with a specific prefix.  They are intended to be nestable.

"""

load("@bazel_skylib//lib:paths.bzl", "paths")

PackageFileInfo = provider(
    fields = {
        "files": "src->dest map",
        "attrs": "file attributes (permissions, etc)",
        "section": "package category",
    },
)

PackageContentsInfo = provider(
    fields = {
        "prefix": "filesystem prefix",
        "prefix_attrs": "attrs to provide to filesystem prefix",
        "children": "Child Providers",
    },
)

def _pkg_file_impl(ctx):
    return [PackageFileInfo(files = {s: paths.basename(s.basename) for s in ctx.files.srcs})]

_pkg_file = rule(
    doc = "Attributes are like existing `pkg_filegroup`",
    implementation = _pkg_file_impl,
    attrs = {
        "srcs": attr.label_list(
            doc = "Source list",
            allow_files = True,
        ),
        "attrs": attr.string_list_dict(
            doc = "Filesystem attributes",
        ),
        "excludes": attr.label_list(
            doc = "Files in 'srcs' to exclude",
            allow_files = True,
        ),
        "renames": attr.label_keyed_string_dict(
            doc = "Label -> destination file name mapping",
            allow_files = True,
        ),
        "strip_prefix": attr.string(
            doc = "Prefix to strip from srcs",
        ),
        "section": attr.string(
            doc = "RPM-style 'section' to provide to pkg_file's provided to `srcs`",
        ),
    },
)

def pkg_file(name, **kwargs):
    _pkg_file(name = name, **kwargs)
    return ":" + name

# Traverse the tree structures created via the pkg_filegroup rules.
#
# This is a depth-first search to find files; intermediate directories are noted
# as they are encountered.
def _pfg_traverse(root):
    stack = [root[PackageContentsInfo]]
    index_stack = [0]
    # TODO: consider also making a "path stack"

    # 1048575 is 2**20 - 1.  Hopefully you won't need more than that many files
    # in your package.  Starlark supports neither recursion nor while loops, so
    # we have to compromise a little. :P
    #
    # What?  It'll finish.  Trust me :)
    for i in range(1048575):
        if index_stack[-1] == 0:
            # The stack is built of PackageContentsInfo's
            path_list = [td.prefix for td in stack] + [""]

            # path_list always has at least two elements in it: the root of the
            # package, and the ending ''
            print(paths.join(path_list[0], *path_list[1:]))

        if index_stack[-1] < len(stack[-1].children):
            current = stack[-1].children[index_stack[-1]]

            # TODO: consider allowing multiple providers to be returned by an
            # individual "srcs" element.
            if PackageFileInfo in current:
                for src, dest in current[PackageFileInfo].files.items():
                    path_list = [se.prefix for se in stack] + [src.basename]
                    print(paths.join(path_list[0], *path_list[1:]))

                # Consume current item
                index_stack[-1] += 1
            else:  # PackageContentsInfo only
                # Go deeper, after consuming the current item
                stack.append(current[PackageContentsInfo])
                index_stack[-1] += 1
                index_stack.append(0)
        else:
            # We've either hit an empty PFG node or we've hit the last one in
            # the files list.
            stack.pop()
            index_stack.pop()
        if len(stack) == 0:
            break

def _pkg_filegroup_impl(ctx):
    return [
        PackageContentsInfo(
            prefix = ctx.attr.prefix,
            prefix_attrs = ctx.attr.prefix_attrs,
            children = ctx.attr.srcs,
        ),
    ]

pkg_filegroup = rule(
    doc = "Attributes are like existing `pkg_filegroup`.  Provides PackageContentsInfo",
    implementation = _pkg_filegroup_impl,
    attrs = {
        "srcs": attr.label_list(
            providers = [[PackageFileInfo], [PackageContentsInfo]],
        ),
        "prefix": attr.string(
            doc = "Prefix to add to any pkg_file's provided to `srcs`",
        ),
        "prefix_attrs": attr.string_list_dict(
            doc = "Attributes to apply to the directory created by 'prefix'",
        ),
    },
)

def _pkg_filegroup_dump(ctx):
    for s in ctx.attr.srcs:
        _pfg_traverse(s)

pkg_filegroup_dump = rule(
    doc = "Dummy rule that prints out the contents of one or more pkg_filegroups",
    implementation = _pkg_filegroup_dump,
    attrs = {
        "srcs": attr.label_list(
            providers = [PackageContentsInfo],
        ),
    },
)
