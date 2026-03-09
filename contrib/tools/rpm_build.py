#!/usr/bin/env python3
# Copyright 2026 The Bazel Authors. All rights reserved.
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
"""Build RPM packages without requiring rpmbuild.

This tool creates RPM packages that can be installed on Linux systems,
without requiring the rpmbuild tool or a Linux build environment.

Usage:
    rpm_build.py --name mypackage --version 1.0 \\
        --file /usr/bin/myapp:./myapp \\
        --file /etc/myapp.conf:./myapp.conf \\
        --output mypackage-1.0-1.noarch.rpm
"""

import argparse
import os
import stat
import sys

from contrib.tools.lib.rpm_writer import RpmWriter


def parse_file_spec(spec):
    """Parse a file specification.

    Format: target_path:source_path[:mode]
    Examples:
        /usr/bin/app:./app
        /etc/config:./config.txt:644
        /usr/share/doc/readme:/dev/null:0644:root:root

    Returns:
        tuple: (target_path, source_path, mode, user, group)
    """
    parts = spec.split(':')
    if len(parts) < 2:
        raise ValueError(f"Invalid file spec '{spec}': need target:source")

    target = parts[0]
    source = parts[1]
    mode = None
    user = "root"
    group = "root"

    if len(parts) >= 3:
        mode_str = parts[2]
        if mode_str:
            mode = int(mode_str, 8)
    if len(parts) >= 4:
        user = parts[3]
    if len(parts) >= 5:
        group = parts[4]

    return target, source, mode, user, group


def parse_dir_spec(spec):
    """Parse a directory specification.

    Format: path[:mode[:user[:group]]]
    Examples:
        /var/lib/myapp
        /etc/myapp.d:755
        /opt/myapp:755:myuser:mygroup

    Returns:
        tuple: (path, mode, user, group)
    """
    parts = spec.split(':')
    path = parts[0]
    mode = 0o755
    user = "root"
    group = "root"

    if len(parts) >= 2 and parts[1]:
        mode = int(parts[1], 8)
    if len(parts) >= 3:
        user = parts[2]
    if len(parts) >= 4:
        group = parts[3]

    return path, mode, user, group


def parse_symlink_spec(spec):
    """Parse a symlink specification.

    Format: link_path:target
    Examples:
        /usr/bin/app:/opt/app/bin/app
        /etc/alternatives/java:/usr/lib/jvm/java-11/bin/java

    Returns:
        tuple: (link_path, target)
    """
    parts = spec.split(':', 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid symlink spec '{spec}': need link:target")
    return parts[0], parts[1]


def main():
    parser = argparse.ArgumentParser(
        description="Build RPM packages without rpmbuild"
    )

    # Package metadata
    parser.add_argument("--name", required=True,
                        help="Package name")
    parser.add_argument("--version", required=True,
                        help="Package version")
    parser.add_argument("--release", default="1",
                        help="Package release (default: 1)")
    parser.add_argument("--arch", default="noarch",
                        help="Target architecture (default: noarch)")
    parser.add_argument("--summary",
                        help="Package summary (defaults to name)")
    parser.add_argument("--description",
                        help="Package description (defaults to summary)")
    parser.add_argument("--license", default="Unknown",
                        help="License (default: Unknown)")
    parser.add_argument("--group", default="Unspecified",
                        help="Package group (default: Unspecified)")

    # Compression
    parser.add_argument("--compression", default="gzip",
                        choices=["gzip", "xz", "bzip2", "none"],
                        help="Payload compression (default: gzip)")

    # Files to include
    parser.add_argument("--file", "-f", action="append", dest="files",
                        metavar="TARGET:SOURCE[:MODE[:USER[:GROUP]]]",
                        help="Add a file: target_path:source_path[:mode[:user[:group]]]")
    parser.add_argument("--dir", "-d", action="append", dest="dirs",
                        metavar="PATH[:MODE[:USER[:GROUP]]]",
                        help="Add a directory: path[:mode[:user[:group]]]")
    parser.add_argument("--symlink", "-s", action="append", dest="symlinks",
                        metavar="LINK:TARGET",
                        help="Add a symlink: link_path:target")

    # Tree input
    parser.add_argument("--tree",
                        help="Add all files from a directory tree with paths relative to it")
    parser.add_argument("--tree-prefix", default="/",
                        help="Prefix for paths when using --tree (default: /)")

    # Output
    parser.add_argument("--output", "-o", required=True,
                        help="Output RPM file path")

    args = parser.parse_args()

    # Create writer
    rpm = RpmWriter(
        name=args.name,
        version=args.version,
        release=args.release,
        arch=args.arch,
        summary=args.summary,
        description=args.description,
        license_text=args.license,
        group=args.group,
        compression=args.compression,
    )

    # Add individual directories
    if args.dirs:
        for spec in args.dirs:
            path, mode, user, group = parse_dir_spec(spec)
            rpm.add_directory(path, mode=mode | stat.S_IFDIR, user=user, group=group)

    # Add individual files
    if args.files:
        for spec in args.files:
            target, source, mode, user, group = parse_file_spec(spec)
            with open(source, 'rb') as f:
                content = f.read()
            if mode is None:
                # Use source file's mode
                mode = os.stat(source).st_mode & 0o7777
            rpm.add_file(target, content, mode=mode | stat.S_IFREG, user=user, group=group)

    # Add individual symlinks
    if args.symlinks:
        for spec in args.symlinks:
            link_path, target = parse_symlink_spec(spec)
            rpm.add_symlink(link_path, target)

    # Add directory tree
    if args.tree:
        prefix = args.tree_prefix.rstrip('/')
        for root, dirs, files in os.walk(args.tree):
            rel_root = os.path.relpath(root, args.tree)
            if rel_root == '.':
                rel_root = ''

            # Add directories
            for d in dirs:
                rel_path = os.path.join(rel_root, d) if rel_root else d
                full_source = os.path.join(root, d)
                mode = os.stat(full_source).st_mode
                target_path = f"{prefix}/{rel_path}"
                rpm.add_directory(target_path, mode=mode)

            # Add files
            for f in files:
                rel_path = os.path.join(rel_root, f) if rel_root else f
                full_source = os.path.join(root, f)

                if os.path.islink(full_source):
                    target = os.readlink(full_source)
                    mode = os.lstat(full_source).st_mode
                    target_path = f"{prefix}/{rel_path}"
                    rpm.add_symlink(target_path, target, mode=mode)
                else:
                    with open(full_source, 'rb') as fh:
                        content = fh.read()
                    mode = os.stat(full_source).st_mode
                    target_path = f"{prefix}/{rel_path}"
                    rpm.add_file(target_path, content, mode=mode)

    # Write RPM
    rpm.write(args.output)
    print(f"Created: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
