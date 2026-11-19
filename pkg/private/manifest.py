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

"""Common package builder manifest helpers
"""

import filecmp
import json


# These must be kept in sync with the declarations in private/pkg_files.bzl
ENTRY_IS_RAW_LINK = "raw_symlink"  # Entry is a file: take content from <src>
ENTRY_IS_FILE = "file"  # Entry is a file: take content from <src>
ENTRY_IS_LINK = "symlink"  # Entry is a symlink: dest -> <src>
ENTRY_IS_DIR = "dir"  # Entry is an empty dir
ENTRY_IS_TREE = "tree" # Entry is a tree artifact: take tree from <src>
ENTRY_IS_EMPTY_FILE = "empty-file"  # Entry is a an empty file

class ManifestEntry(object):
    """Structured wrapper around rules_pkg-produced manifest entries"""
    type: str
    dest: str
    src: str
    mode: str
    user: str
    group: str
    uid: int
    gid: int
    origin: str = None
    repository: str = None

    def __init__(self, type, dest, src, mode, user, group, uid = None, gid = None, origin = None, repository = None):
        self.type = type
        self.dest = dest
        self.src = src
        self.mode = mode
        self.user = user
        self.group = group
        self.uid = uid
        self.gid = gid
        self.origin = origin
        self.repository = repository

    def __repr__(self):
        return "ManifestEntry<{}>".format(vars(self))

def read_entries_from(path):
    """Return a list of ManifestEntry's from the manifest file at `path`"""
    # Subtle: decode the content with read() rather than in json.load() because
    # the load in older python releases (< 3.7?) does not know how to decode.
    # Moreover, prior to Bazel 8 (bazelbuild/bazel#24231), non-ASCII characters
    # led files to be UTF-16LE-encoded on Windows.
    with open(path, "rb") as fh:
        raw = fh.read()
    raw_entries = json.loads(raw.decode("utf-16-le" if raw[1:2] == b"\0" else "utf-8"))
    return [ManifestEntry(**entry) for entry in raw_entries]

def entry_type_to_string(et):
    """Entry type stringifier"""
    if et == ENTRY_IS_FILE:
        return "file"
    elif et == ENTRY_IS_LINK:
        return "symlink",
    elif et == ENTRY_IS_DIR:
        return "directory"
    elif et == ENTRY_IS_TREE:
        return "tree"
    elif et == ENTRY_IS_EMPTY_FILE:
        return "empty_file"
    else:
        raise ValueError("Invalid entry id {}".format(et))


class TreeFileTracker(object):
    """Detects conflicting paths provided by several tree artifacts."""

    def __init__(self):
        self._seen = {}

    def add_file(self, dest, content_path, tree):
        """Records the file at dest, and returns whether it must be written.

        Raises:
          ValueError: dest was already provided by another tree as a directory
            or as a file with different content.
        """
        previous = self._seen.get(dest)
        if previous is None:
            self._seen[dest] = (content_path, tree)
            return True
        previous_path, previous_tree = previous
        if previous_path is not None and filecmp.cmp(previous_path, content_path, shallow=False):
            return False
        raise ValueError(
            "Conflicting path %s, provided by tree artifacts %s and %s" %
            (dest, previous_tree, tree))

    def add_dir(self, dest, tree):
        """Records the directory at dest.

        Raises:
          ValueError: dest was already provided by another tree as a file.
        """
        dest = dest.rstrip("/")
        previous = self._seen.get(dest)
        if previous is None:
            self._seen[dest] = (None, tree)
        elif previous[0] is not None:
            raise ValueError(
                "Conflicting path %s, provided by tree artifacts %s and %s" %
                (dest, previous[1], tree))
