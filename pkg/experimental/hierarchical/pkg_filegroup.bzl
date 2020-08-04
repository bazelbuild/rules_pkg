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
        "transitive": "Child Providers",
    },
)

def _pkg_file_impl(ctx):
    return [PkgFileInfo(file_dest_map = {s: "" for s in ctx.attr.srcs})]

_pkg_file = rule(
    doc = "Attributes are like existing `pkg_filegroup`",
    implementation = _pkg_file_impl,
    attrs = {
        "srcs": attr.label_list(
            "Source list",
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

def _pkg_filegroup_impl(ctx):
    for s in ctx.attr.srcs:
        print(s[PkgFileInfo].file_dest_map)
    return [
        PackageContentsInfo(
            prefix = ctx.attr.prefix,
            prefix_attrs = ctx.attr.prefix_attrs,
            transitive = depset([], transitive = srcs),
        ),
    ]

pkg_filegroup = rule(
    doc = "Attributes are like existing `pkg_filegroup`.  Provides PackageContentsInfo",
    implementation = _pkg_filegroup_impl,
    attrs = {
        "data": attr.label_list(
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
