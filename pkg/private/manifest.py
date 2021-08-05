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

import collections

# These must be kept in sync with the declarations in private/pkg_files.bzl
ENTRY_IS_FILE = 0  # Entry is a file: take content from <src>
ENTRY_IS_LINK = 1  # Entry is a symlink: dest -> <src>
ENTRY_IS_DIR = 2  # Entry is an owned dir, possibly empty
ENTRY_IS_TREE = 3  # Entry is a tree artifact: take tree from <src>
ENTRY_IS_EMPTY_FILE = 4  # Entry is a an empty file

ManifestEntry = collections.namedtuple("ManifestEntry",
                                       ['entry_type', 'dest', 'src', 'mode', 'user', 'group'])


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
