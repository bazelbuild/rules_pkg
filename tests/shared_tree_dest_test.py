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

import json
import os
import subprocess
import tempfile
import unittest

from pkg.private import manifest
from python.runfiles import runfiles


def _make_tree(root, name, files):
  tree = os.path.join(root, name)
  for path, content in files.items():
    full = os.path.join(tree, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
      f.write(content)
  return tree


def _write_manifest(root, trees):
  path = os.path.join(root, "manifest.json")
  with open(path, "w") as f:
    json.dump([{
        "type": manifest.ENTRY_IS_TREE,
        "dest": "include",
        "src": tree,
        "mode": "",
        "user": None,
        "group": None,
        "uid": None,
        "gid": None,
        "origin": "@//:" + os.path.basename(tree),
        "repository": None,
    } for tree in trees], f)
  return path


class TreeFileTrackerTest(unittest.TestCase):

  def setUp(self):
    self.root = tempfile.mkdtemp(dir=os.getenv("TEST_TMPDIR"))
    self.tracker = manifest.TreeFileTracker()

  def _file(self, tree, path, content):
    return os.path.join(_make_tree(self.root, tree, {path: content}), path)

  def test_distinct_files(self):
    self.assertTrue(self.tracker.add_file("include/a.h", self._file("a", "a.h", "a"), "a"))
    self.assertTrue(self.tracker.add_file("include/b.h", self._file("b", "b.h", "b"), "b"))

  def test_identical_file(self):
    self.assertTrue(self.tracker.add_file("include/x.h", self._file("a", "x.h", "same"), "a"))
    self.assertFalse(self.tracker.add_file("include/x.h", self._file("b", "x.h", "same"), "b"))

  def test_conflicting_file(self):
    self.tracker.add_file("include/x.h", self._file("a", "x.h", "a"), "a")
    with self.assertRaisesRegex(ValueError, "Conflicting path include/x.h"):
      self.tracker.add_file("include/x.h", self._file("b", "x.h", "b"), "b")

  def test_shared_dir(self):
    self.tracker.add_dir("include/x", "a")
    self.tracker.add_dir("include/x/", "b")

  def test_file_then_dir(self):
    self.tracker.add_file("include/x", self._file("a", "x", "a"), "a")
    with self.assertRaisesRegex(ValueError, "Conflicting path include/x"):
      self.tracker.add_dir("include/x/", "b")

  def test_dir_then_file(self):
    self.tracker.add_dir("include/x", "a")
    with self.assertRaisesRegex(ValueError, "Conflicting path include/x"):
      self.tracker.add_file("include/x", self._file("b", "x", "b"), "b")


class WriterConflictTest(unittest.TestCase):

  def setUp(self):
    self.runfiles = runfiles.Create()
    self.root = tempfile.mkdtemp(dir=os.getenv("TEST_TMPDIR"))

  def _run(self, binary, args):
    env = dict(os.environ)
    env.update(self.runfiles.EnvVars())
    return subprocess.run(
        [self.runfiles.Rlocation("rules_pkg/pkg/private/" + binary)] + args,
        env=env, capture_output=True, text=True)

  def _check(self, binary, make_args):
    out = os.path.join(self.root, "out")
    ok = _write_manifest(self.root, [
        _make_tree(self.root, "ok_a", {"a.h": "a", "x.h": "same"}),
        _make_tree(self.root, "ok_b", {"b/b.h": "b", "x.h": "same"}),
    ])
    result = self._run(binary, make_args(out, ok))
    self.assertEqual(result.returncode, 0, result.stderr)

    for name, trees in (("file", ({"x.h": "a"}, {"x.h": "b"})),
                        ("file_dir", ({"x": "a"}, {"x/y": "b"})),
                        ("dir_file", ({"x/y": "b"}, {"x": "a"}))):
      conflict = _write_manifest(self.root, [
          _make_tree(self.root, name + "_a", trees[0]),
          _make_tree(self.root, name + "_b", trees[1]),
      ])
      result = self._run(binary, make_args(out, conflict))
      self.assertNotEqual(result.returncode, 0, name)
      self.assertIn("Conflicting path include/x", result.stderr, name)

  def test_tar(self):
    self._check("tar/build_tar",
                lambda out, m: ["--output", out + ".tar", "--directory", "/", "--manifest", m])

  def test_zip(self):
    self._check("zip/build_zip",
                lambda out, m: ["--output", out + ".zip", "-m", "0644", "-c", "deflated", "-l", "6", "--manifest", m])


if __name__ == "__main__":
  unittest.main()
