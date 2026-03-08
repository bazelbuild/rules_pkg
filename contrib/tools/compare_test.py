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
"""Tests for tree_size_compare comparison functionality."""

import unittest

from python.runfiles import runfiles

from contrib.tools.lib.tar_reader import TarReader
from contrib.tools.tree_size_compare import (
    stream_compare,
    load_tree_from_reader,
    check_size_threshold,
    should_include_path,
)


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


class StreamCompareTest(unittest.TestCase):
    """Test the stream_compare function directly."""

    def _default_flags(self, **overrides):
        """Return default flags dict with optional overrides."""
        flags = {
            "max_allowed_absolute_increase": 0,
            "max_allowed_percent_increase": 100,
            "show_decreases": True,
            "minimum_compare_size": 0,
            "include_patterns": [],
            "exclude_patterns": [],
            "compare_uid_gid": True,
        }
        flags.update(overrides)
        return flags

    def test_stream_compare_identical(self):
        """stream_compare reports no differences for identical trees."""
        tar_path = get_runfile("contrib/tools/testdata/reference_tar.tar")

        expected = load_tree_from_reader(TarReader(tar_path=tar_path))
        got_reader = TarReader(tar_path=tar_path)

        results = stream_compare(expected, got_reader, self._default_flags())

        self.assertEqual(results["only_in_expected"], [])
        self.assertEqual(results["only_in_got"], [])
        self.assertEqual(results["symlink_target_changed"], [])
        self.assertEqual(results["metadata_changed"], [])
        self.assertEqual(results["size_changed"], [])

    def test_stream_compare_missing_files(self):
        """stream_compare detects files only in expected."""
        ref_path = get_runfile("contrib/tools/testdata/reference_tar.tar")
        mod_path = get_runfile("contrib/tools/testdata/modified_tar.tar")

        expected = load_tree_from_reader(TarReader(tar_path=ref_path))
        got_reader = TarReader(tar_path=mod_path)

        results = stream_compare(expected, got_reader, self._default_flags())

        missing_paths = [path for path, _ in results["only_in_expected"]]
        self.assertIn("subdir/nested.txt", missing_paths)
        self.assertIn("subdir", missing_paths)
        self.assertIn("link_to_hello", missing_paths)

    def test_stream_compare_extra_files(self):
        """stream_compare detects files only in got."""
        ref_path = get_runfile("contrib/tools/testdata/reference_tar.tar")
        extra_path = get_runfile("contrib/tools/testdata/extra_file_tar.tar")

        expected = load_tree_from_reader(TarReader(tar_path=ref_path))
        got_reader = TarReader(tar_path=extra_path)

        results = stream_compare(expected, got_reader, self._default_flags())

        extra_paths = [path for path, _ in results["only_in_got"]]
        self.assertIn("extra/hello.txt", extra_paths)

    def test_stream_compare_mode_change(self):
        """stream_compare detects mode changes."""
        ref_path = get_runfile("contrib/tools/testdata/reference_tar.tar")
        diff_path = get_runfile("contrib/tools/testdata/different_mode_tar.tar")

        expected = load_tree_from_reader(TarReader(tar_path=ref_path))
        got_reader = TarReader(tar_path=diff_path)

        results = stream_compare(expected, got_reader, self._default_flags())

        # Should have metadata changes for files with different mode
        changed_paths = [path for path, _ in results["metadata_changed"]]
        self.assertIn("hello.txt", changed_paths)

    def test_stream_compare_uid_gid_change(self):
        """stream_compare detects uid/gid changes when enabled."""
        ref_path = get_runfile("contrib/tools/testdata/reference_tar.tar")
        diff_path = get_runfile("contrib/tools/testdata/different_owner_tar.tar")

        expected = load_tree_from_reader(TarReader(tar_path=ref_path))
        got_reader = TarReader(tar_path=diff_path)

        results = stream_compare(expected, got_reader, self._default_flags(compare_uid_gid=True))

        # Should have metadata changes for files with different uid/gid
        changed_paths = [path for path, _ in results["metadata_changed"]]
        self.assertIn("hello.txt", changed_paths)

    def test_stream_compare_uid_gid_ignored(self):
        """stream_compare ignores uid/gid changes when disabled."""
        ref_path = get_runfile("contrib/tools/testdata/reference_tar.tar")
        diff_path = get_runfile("contrib/tools/testdata/different_owner_tar.tar")

        expected = load_tree_from_reader(TarReader(tar_path=ref_path))
        got_reader = TarReader(tar_path=diff_path)

        results = stream_compare(expected, got_reader, self._default_flags(compare_uid_gid=False))

        # Should NOT have metadata changes since uid/gid comparison is disabled
        self.assertEqual(results["metadata_changed"], [])

    def test_stream_compare_symlink_target_change(self):
        """stream_compare detects symlink target changes."""
        ref_path = get_runfile("contrib/tools/testdata/reference_tar.tar")
        diff_path = get_runfile("contrib/tools/testdata/different_symlink_tar.tar")

        expected = load_tree_from_reader(TarReader(tar_path=ref_path))
        got_reader = TarReader(tar_path=diff_path)

        results = stream_compare(expected, got_reader, self._default_flags())

        # Should detect symlink target change
        self.assertEqual(len(results["symlink_target_changed"]), 1)
        path, old_target, new_target = results["symlink_target_changed"][0]
        self.assertEqual(path, "link_to_hello")
        self.assertEqual(old_target, "hello.txt")
        self.assertEqual(new_target, "subdir/nested.txt")

    def test_stream_compare_include_pattern(self):
        """stream_compare respects include patterns."""
        ref_path = get_runfile("contrib/tools/testdata/reference_tar.tar")
        extra_path = get_runfile("contrib/tools/testdata/extra_file_tar.tar")

        expected = load_tree_from_reader(TarReader(tar_path=ref_path))
        got_reader = TarReader(tar_path=extra_path)

        # Only include files matching "hello"
        results = stream_compare(expected, got_reader,
                                 self._default_flags(include_patterns=["hello"]))

        # extra/hello.txt should be reported since it matches the pattern
        extra_paths = [path for path, _ in results["only_in_got"]]
        self.assertIn("extra/hello.txt", extra_paths)

        # Files not matching pattern should not be reported as missing
        missing_paths = [path for path, _ in results["only_in_expected"]]
        self.assertNotIn("subdir", missing_paths)

    def test_stream_compare_exclude_pattern(self):
        """stream_compare respects exclude patterns."""
        ref_path = get_runfile("contrib/tools/testdata/reference_tar.tar")
        extra_path = get_runfile("contrib/tools/testdata/extra_file_tar.tar")

        expected = load_tree_from_reader(TarReader(tar_path=ref_path))
        got_reader = TarReader(tar_path=extra_path)

        # Exclude files matching "extra"
        results = stream_compare(expected, got_reader,
                                 self._default_flags(exclude_patterns=["extra"]))

        # extra/hello.txt should NOT be reported since it's excluded
        extra_paths = [path for path, _ in results["only_in_got"]]
        self.assertNotIn("extra/hello.txt", extra_paths)


class SizeThresholdTest(unittest.TestCase):
    """Test size threshold checking."""

    def _default_flags(self, **overrides):
        """Return default flags dict with optional overrides."""
        flags = {
            "max_allowed_absolute_increase": 0,
            "max_allowed_percent_increase": 100,
            "show_decreases": True,
            "minimum_compare_size": 0,
        }
        flags.update(overrides)
        return flags

    def test_absolute_increase_threshold(self):
        """Detects when size increase exceeds absolute threshold."""
        flags = self._default_flags(max_allowed_absolute_increase=100)

        # Under threshold - passes
        passed, msg = check_size_threshold(1000, 1050, flags)
        self.assertTrue(passed)

        # Over threshold - fails
        passed, msg = check_size_threshold(1000, 1200, flags)
        self.assertFalse(passed)
        self.assertIn("200 bytes", msg)

    def test_percent_increase_threshold(self):
        """Detects when size increase exceeds percent threshold."""
        flags = self._default_flags(max_allowed_percent_increase=10)

        # Under threshold - passes
        passed, msg = check_size_threshold(1000, 1050, flags)
        self.assertTrue(passed)

        # Over threshold - fails
        passed, msg = check_size_threshold(1000, 1200, flags)
        self.assertFalse(passed)
        self.assertIn("20.00%", msg)

    def test_minimum_compare_size(self):
        """Files below minimum_compare_size are not checked."""
        flags = self._default_flags(
            max_allowed_percent_increase=10,
            minimum_compare_size=500
        )

        # Small files pass even with large percent change
        passed, msg = check_size_threshold(100, 200, flags)
        self.assertTrue(passed)

        # Large files fail with same percent change
        passed, msg = check_size_threshold(1000, 2000, flags)
        self.assertFalse(passed)

    def test_show_decreases_false(self):
        """Size decreases are ignored when show_decreases=False."""
        flags = self._default_flags(
            max_allowed_percent_increase=10,
            show_decreases=False
        )

        # Decrease passes regardless of magnitude
        passed, msg = check_size_threshold(1000, 100, flags)
        self.assertTrue(passed)

    def test_show_decreases_true(self):
        """Size decreases are checked when show_decreases=True."""
        flags = self._default_flags(
            max_allowed_percent_increase=10,
            show_decreases=True
        )

        # Decrease is shown (but won't fail percent check since it's negative)
        passed, msg = check_size_threshold(1000, 100, flags)
        self.assertTrue(passed)  # Negative percent doesn't exceed positive threshold


class FilterPatternTest(unittest.TestCase):
    """Test include/exclude pattern filtering."""

    def test_include_pattern_match(self):
        """Paths matching include pattern are included."""
        self.assertTrue(should_include_path("foo/bar.txt", ["bar"], []))
        self.assertTrue(should_include_path("foo/bar.txt", ["foo"], []))
        self.assertTrue(should_include_path("foo/bar.txt", [r"\.txt$"], []))

    def test_include_pattern_no_match(self):
        """Paths not matching include pattern are excluded."""
        self.assertFalse(should_include_path("foo/bar.txt", ["baz"], []))
        self.assertFalse(should_include_path("foo/bar.txt", [r"\.py$"], []))

    def test_exclude_pattern_match(self):
        """Paths matching exclude pattern are excluded."""
        self.assertFalse(should_include_path("foo/bar.txt", [], ["bar"]))
        self.assertFalse(should_include_path("foo/bar.txt", [], [r"\.txt$"]))

    def test_exclude_pattern_no_match(self):
        """Paths not matching exclude pattern are included."""
        self.assertTrue(should_include_path("foo/bar.txt", [], ["baz"]))
        self.assertTrue(should_include_path("foo/bar.txt", [], [r"\.py$"]))

    def test_no_patterns(self):
        """All paths included when no patterns specified."""
        self.assertTrue(should_include_path("anything/at/all.txt", [], []))

    def test_include_and_exclude(self):
        """Both include and exclude patterns are applied."""
        # Matches include but also matches exclude - excluded
        self.assertFalse(should_include_path("foo/bar.txt", ["foo"], ["bar"]))

        # Matches include and doesn't match exclude - included
        self.assertTrue(should_include_path("foo/baz.txt", ["foo"], ["bar"]))


class MetadataDetectionTest(unittest.TestCase):
    """Test detection of metadata changes between trees."""

    def test_detects_missing_file(self):
        """Detects files in expected but not in got."""
        ref_path = get_runfile("contrib/tools/testdata/reference_tar.tar")
        mod_path = get_runfile("contrib/tools/testdata/modified_tar.tar")

        expected = load_tree_as_dict(TarReader(tar_path=ref_path))
        got = load_tree_as_dict(TarReader(tar_path=mod_path))

        # modified_tar has fewer files than reference_tar
        missing = set(expected.keys()) - set(got.keys())
        self.assertIn("subdir/nested.txt", missing)
        self.assertIn("subdir", missing)
        self.assertIn("link_to_hello", missing)

    def test_detects_extra_file(self):
        """Detects files in got but not in expected."""
        ref_path = get_runfile("contrib/tools/testdata/reference_tar.tar")
        extra_path = get_runfile("contrib/tools/testdata/extra_file_tar.tar")

        expected = load_tree_as_dict(TarReader(tar_path=ref_path))
        got = load_tree_as_dict(TarReader(tar_path=extra_path))

        extra = set(got.keys()) - set(expected.keys())
        self.assertIn("extra/hello.txt", extra)

    def test_detects_mode_change(self):
        """Detects files with different mode."""
        ref_path = get_runfile("contrib/tools/testdata/reference_tar.tar")
        diff_path = get_runfile("contrib/tools/testdata/different_mode_tar.tar")

        expected = load_tree_as_dict(TarReader(tar_path=ref_path))
        got = load_tree_as_dict(TarReader(tar_path=diff_path))

        # hello.txt should have different mode
        self.assertNotEqual(expected["hello.txt"].mode, got["hello.txt"].mode)

    def test_detects_owner_change(self):
        """Detects files with different uid/gid."""
        ref_path = get_runfile("contrib/tools/testdata/reference_tar.tar")
        diff_path = get_runfile("contrib/tools/testdata/different_owner_tar.tar")

        expected = load_tree_as_dict(TarReader(tar_path=ref_path))
        got = load_tree_as_dict(TarReader(tar_path=diff_path))

        # hello.txt should have different uid/gid
        self.assertNotEqual(expected["hello.txt"].uid, got["hello.txt"].uid)
        self.assertNotEqual(expected["hello.txt"].gid, got["hello.txt"].gid)

    def test_detects_symlink_target_change(self):
        """Detects symlinks with different targets."""
        ref_path = get_runfile("contrib/tools/testdata/reference_tar.tar")
        diff_path = get_runfile("contrib/tools/testdata/different_symlink_tar.tar")

        expected = load_tree_as_dict(TarReader(tar_path=ref_path))
        got = load_tree_as_dict(TarReader(tar_path=diff_path))

        # link_to_hello should have different target
        self.assertTrue(expected["link_to_hello"].is_symlink)
        self.assertTrue(got["link_to_hello"].is_symlink)
        self.assertNotEqual(
            expected["link_to_hello"].symlink_target,
            got["link_to_hello"].symlink_target
        )


if __name__ == "__main__":
    unittest.main()
