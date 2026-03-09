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
"""Tests for the various TreeReader implementations."""

import json
import os
import tempfile
import unittest

from python.runfiles import runfiles

from contrib.tools.lib.deb_reader import DebReader
from contrib.tools.lib.saved_tree import SavedTreeReader
from contrib.tools.lib.tar_reader import TarReader


def get_runfile(path):
    """Get the path to a runfile."""
    r = runfiles.Create()
    return r.Rlocation("_main/" + path)


def load_tree_as_dict(reader):
    """Load all items from a reader into a dict keyed by path."""
    result = {}
    while True:
        item = reader.next()
        if item is None:
            break
        result[item.path] = item
    return result


class TarReaderTest(unittest.TestCase):
    """Test TarReader functionality."""

    def test_tar_reader_loads_reference(self):
        """TarReader can load the reference tar file."""
        tar_path = get_runfile("contrib/tools/testdata/reference_tar.tar")
        reader = TarReader(tar_path=tar_path)
        tree = load_tree_as_dict(reader)

        self.assertIn("hello.txt", tree)
        self.assertIn("subdir", tree)
        self.assertIn("subdir/nested.txt", tree)
        self.assertIn("link_to_hello", tree)

    def test_tar_gz_reader_loads_reference(self):
        """TarReader can load gzip-compressed tar."""
        tar_path = get_runfile("contrib/tools/testdata/reference_tar_gz.tar.gz")
        reader = TarReader(tar_path=tar_path)
        tree = load_tree_as_dict(reader)

        self.assertIn("hello.txt", tree)
        self.assertEqual(tree["hello.txt"].size, 14)

    def test_tar_xz_reader_loads_reference(self):
        """TarReader can load xz-compressed tar."""
        tar_path = get_runfile("contrib/tools/testdata/reference_tar_xz.tar.xz")
        reader = TarReader(tar_path=tar_path)
        tree = load_tree_as_dict(reader)

        self.assertIn("hello.txt", tree)

    def test_tar_formats_produce_same_content(self):
        """All tar compression formats produce the same logical tree."""
        tar_path = get_runfile("contrib/tools/testdata/reference_tar.tar")
        gz_path = get_runfile("contrib/tools/testdata/reference_tar_gz.tar.gz")
        xz_path = get_runfile("contrib/tools/testdata/reference_tar_xz.tar.xz")

        tree_tar = load_tree_as_dict(TarReader(tar_path=tar_path))
        tree_gz = load_tree_as_dict(TarReader(tar_path=gz_path))
        tree_xz = load_tree_as_dict(TarReader(tar_path=xz_path))

        # Same paths
        self.assertEqual(set(tree_tar.keys()), set(tree_gz.keys()))
        self.assertEqual(set(tree_tar.keys()), set(tree_xz.keys()))

        # Same metadata for each file
        for path in tree_tar:
            self.assertEqual(tree_tar[path].size, tree_gz[path].size)
            self.assertEqual(tree_tar[path].size, tree_xz[path].size)
            self.assertEqual(tree_tar[path].is_dir, tree_gz[path].is_dir)
            self.assertEqual(tree_tar[path].is_symlink, tree_gz[path].is_symlink)

    def test_paths_have_no_dot_slash_prefix(self):
        """TarReader strips the ./ prefix from paths."""
        tar_path = get_runfile("contrib/tools/testdata/reference_tar.tar")
        tree = load_tree_as_dict(TarReader(tar_path=tar_path))

        for path in tree:
            self.assertFalse(path.startswith("./"),
                             f"Path should not start with './': {path}")

    def test_symlink_properties(self):
        """Symlinks are correctly identified."""
        tar_path = get_runfile("contrib/tools/testdata/reference_tar.tar")
        tree = load_tree_as_dict(TarReader(tar_path=tar_path))

        link = tree["link_to_hello"]
        self.assertTrue(link.is_symlink)
        self.assertEqual(link.symlink_target, "hello.txt")
        self.assertEqual(link.size, 0)  # Symlinks have size 0

    def test_directory_properties(self):
        """Directories are correctly identified."""
        tar_path = get_runfile("contrib/tools/testdata/reference_tar.tar")
        tree = load_tree_as_dict(TarReader(tar_path=tar_path))

        subdir = tree["subdir"]
        self.assertTrue(subdir.is_dir)
        self.assertFalse(subdir.is_symlink)
        self.assertEqual(subdir.size, 0)  # Directories have size 0


class SavedTreeReaderTest(unittest.TestCase):
    """Test SavedTreeReader functionality."""

    def test_save_and_load_json(self):
        """SavedTreeReader can load a tree saved as JSON."""
        tar_path = get_runfile("contrib/tools/testdata/reference_tar.tar")
        tree = load_tree_as_dict(TarReader(tar_path=tar_path))

        # Convert to list of dicts for saving
        items = []
        for info in tree.values():
            d = {"path": info.path, "mode": oct(info.mode)[2:]}
            if info.uid != 0:
                d["uid"] = info.uid
            if info.gid != 0:
                d["gid"] = info.gid
            if info.is_symlink:
                d["is_symlink"] = True
                d["target"] = info.symlink_target
            elif info.is_dir:
                d["is_dir"] = True
            else:
                d["size"] = info.size
            items.append(d)

        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(items, f)
            json_path = f.name

        try:
            # Load back
            loaded = load_tree_as_dict(SavedTreeReader(json_path))

            # Compare
            self.assertEqual(set(tree.keys()), set(loaded.keys()))
            for path in tree:
                self.assertEqual(tree[path].size, loaded[path].size)
                self.assertEqual(tree[path].is_dir, loaded[path].is_dir)
                self.assertEqual(tree[path].is_symlink, loaded[path].is_symlink)
        finally:
            os.unlink(json_path)


class DebReaderTest(unittest.TestCase):
    """Test DebReader functionality."""

    def test_deb_reader_loads_package(self):
        """DebReader can load a .deb package."""
        deb_path = get_runfile("contrib/tools/testdata/test_deb.deb")
        reader = DebReader(deb_path)
        tree = load_tree_as_dict(reader)

        # Should have files from the deb
        self.assertIn("usr/fizzbuzz", tree)
        self.assertIn("etc/nsswitch.conf", tree)

    def test_deb_reader_symlinks(self):
        """DebReader correctly identifies symlinks in .deb."""
        deb_path = get_runfile("contrib/tools/testdata/test_deb.deb")
        reader = DebReader(deb_path)
        tree = load_tree_as_dict(reader)

        # Should have the java symlink
        self.assertIn("usr/bin/java", tree)
        java_link = tree["usr/bin/java"]
        self.assertTrue(java_link.is_symlink)
        self.assertEqual(java_link.symlink_target, "/path/to/bin/java")

    def test_deb_reader_paths_normalized(self):
        """DebReader paths have no ./ prefix."""
        deb_path = get_runfile("contrib/tools/testdata/test_deb.deb")
        reader = DebReader(deb_path)
        tree = load_tree_as_dict(reader)

        for path in tree:
            self.assertFalse(path.startswith("./"),
                             f"Path should not start with './': {path}")


if __name__ == "__main__":
    unittest.main()
