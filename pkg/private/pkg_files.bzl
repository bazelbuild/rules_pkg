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
"""Internal methods for processing pkg_file* instances."""

load(
    "//:providers.bzl",
    "PackageArtifactInfo",
    "PackageDirsInfo",
    "PackageFilegroupInfo",
    "PackageFilesInfo",
    "PackageSymlinkInfo",
)

_DestFile = provider(
    doc = """Information about each destination in the final package.""",
    fields = {
        "src": "source file",
        "mode": "mode, or empty",
        "owner": "owner, or empty",
        "group": "group, or empty",
        "link_to": "path to link to. src must not be set",
        "is_dir": "path to create a dirctory. src must not be set",
        "origin": "target which added this",
    },
)

# 0xef 0xbf 0xbf => 0357 0277 0277
_vbar_esc = "\357\277\277"

def pr_file(dest, df):
    if len(_vbar_esc) != 3:
        fail("Starlark octal escaping is broken")
    if _vbar_esc in dest:
        fail("Unusable source file <%s>" % dest)
    ret = dest.replace("|", _vbar_esc) + "|"
    if df.src:
        # Very subtle escaping of '|'. Transpose to a Unicode Noncharacter.
        # http://www.unicode.org/faq/private_use.html#nonchar1
        # We pick 0xffff because it is easy to spot. The utf-8 encoding of that
        # is 0xef 0xbf 0xbf. We can replace that directly into a starlark
        # string, and when we write it out it will be perfectly encoded in
        # UTF-8
        # Why this works: No one can use a Noncharacter in a valid file name.
        # Well, they might be able create the file, but it is not likely to
        # be usable with others. We protect ourselves by simply failing if
        # someone tries to do this horrible thing.
        if _vbar_esc in df.src.path:
            fail("Unusable source file <%s>" % df.src.path)
        ret += df.src.path.replace("|", _vbar_esc)
    ret += "|%s|%s|%s|%s|%s\n" % (
        df.mode or "",
        df.owner or "",
        df.group or "",
        df.link_to if hasattr(df, "link_to") else "",
        df.is_dir if hasattr(df, "is_dir") else "",
    )
    return ret

def _check_dest(out_spec, dest, origin):
    if dest in out_spec:
        fail("Duplicate output path: <%s>, declared in %s and %s" % (
            dest,
            origin,
            out_spec[dest].origin,
        ))

def _merge_attributes(info, mode, owner, group):
    if hasattr(info, "attributes"):
        attrs = info.attributes
        mode = attrs.get("mode") or mode
        owner = attrs.get("owner") or owner
        group = attrs.get("group") or group
    return (mode, owner, group)

def _process_pkg_dirs(out_spec, pkg_dirs_info, origin, default_mode, default_owner, default_group):
    attrs = _merge_attributes(pkg_dirs_info, default_mode, default_owner, default_group)
    for dest in pkg_dirs_info.dirs:
        _check_dest(out_spec, dest, origin)
        out_spec[dest] = _DestFile(
            src = None,
            is_dir = 1,
            mode = attrs[0],
            owner = attrs[1],
            group = attrs[2],
            origin = origin,
        )

def _process_pkg_files(out_spec, pkg_files_info, origin, default_mode, default_owner, default_group):
    attrs = _merge_attributes(pkg_files_info, default_mode, default_owner, default_group)
    for dest, src in pkg_files_info.dest_src_map.items():
        _check_dest(out_spec, dest, origin)
        out_spec[dest] = _DestFile(
            src = src,
            mode = attrs[0],
            owner = attrs[1],
            group = attrs[2],
            origin = origin,
        )

def _process_pkg_symlink(out_spec, pkg_symlink_info, origin, default_mode, default_owner, default_group):
    dest = pkg_symlink_info.destination
    attrs = _merge_attributes(pkg_symlink_info, default_mode, default_owner, default_group)
    _check_dest(out_spec, dest, origin)
    out_spec[dest] = _DestFile(
        src = None,
        mode = attrs[0],
        owner = attrs[1],
        group = attrs[2],
        origin = origin,
        link_to = pkg_symlink_info.source,
    )

def _process_pkg_filegroup(out_spec, pkg_filegroup_info, origin, default_mode, default_owner, default_group):
    for d in pkg_filegroup_info.pkg_dirs:
        _process_pkg_dirs(out_spec, d[0], d[1], default_mode, default_owner, default_group)
    for pf in pkg_filegroup_info.pkg_files:
        _process_pkg_files(out_spec, pf[0], pf[1], default_mode, default_owner, default_group)
    for psl in pkg_filegroup_info.pkg_symlinks:
        _process_pkg_symlink(out_spec, psl[0], psl[1], default_mode, default_owner, default_group)

def process_src(out_spec, src, origin, default_mode, default_owner, default_group):
    """Add a source target to the content map.

    Returns:
      True if src was a Package*Info and completely processed.
      False if we did not process it.
    """
    if PackageFilesInfo in src:
        _process_pkg_files(
            out_spec,
            src[PackageFilesInfo],
            origin,
            default_mode,
            default_owner,
            default_group,
        )
    elif PackageFilegroupInfo in src:
        _process_pkg_filegroup(
            out_spec,
            src[PackageFilegroupInfo],
            origin,
            default_mode,
            default_owner,
            default_group,
        )
    elif PackageSymlinkInfo in src:
        _process_pkg_symlink(
            out_spec,
            src[PackageSymlinkInfo],
            origin,
            default_mode,
            default_owner,
            default_group,
        )
    elif PackageDirsInfo in src:
        _process_pkg_dirs(
            out_spec,
            src[PackageDirsInfo],
            origin,
            "0555",
            default_owner,
            default_group,
        )
    else:
        return False
    return True

def write_manifest(ctx, ofile, out_spec):
    #for dst in sorted(out_spec.keys()):
    #  print(pr_file(out_spec[dst]))
    ctx.actions.write(
        ofile,
        "".join([
            pr_file(dst, out_spec[dst])
            for dst in sorted(out_spec.keys())
        ]),
    )
