# Copyright 2015 The Bazel Authors. All rights reserved.
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
"""Testing for build_tar."""

import os
import unittest

from bazel_tools.tools.python.runfiles import runfiles
from pkg.private.tar import build_tar
from tests.tar import helper


class TarFileUnitTest(unittest.TestCase):
  """Unit testing for TarFile class."""

  def setUp(self):
    super(TarFileUnitTest, self).setUp()
    self.tempfile = os.path.join(os.environ["TEST_TMPDIR"], "test.tar")
    self.data_files = runfiles.Create()
    # Keep the trailing slash stripped. Add slash manually when needed.
    self.directory = self.data_files.Rlocation("rules_pkg/tests/testdata/").strip('/')

  def tearDown(self):
    super(TarFileUnitTest, self).tearDown()
    if os.path.exists(self.tempfile):
      os.remove(self.tempfile)

  def test_normalize_path(self):
    path_without_leading_period = os.path.sep.join(("foo", "bar", ""))
    path_with_leading_period = os.path.sep.join((".", "foo", "bar", ""))
    with build_tar.TarFile(self.tempfile, self.directory, "", "", None) as tar_file_obj:
      self.assertEqual(tar_file_obj.normalize_path(path_without_leading_period), self.directory + "/foo/bar")
      self.assertEqual(tar_file_obj.normalize_path(path_with_leading_period), self.directory + "/foo/bar")
    with build_tar.TarFile(self.tempfile, self.directory + "/", "", "", None) as tar_file_obj:
      self.assertEqual(tar_file_obj.normalize_path(path_without_leading_period), self.directory + "/foo/bar")
      self.assertEqual(tar_file_obj.normalize_path(path_with_leading_period), self.directory + "/foo/bar")
    with build_tar.TarFile(self.tempfile, "/", "", "", None) as tar_file_obj:
      self.assertEqual(tar_file_obj.normalize_path(path_without_leading_period), "foo/bar")
      self.assertEqual(tar_file_obj.normalize_path(path_with_leading_period), "foo/bar")

  def test_add_tree(self):
    with build_tar.TarFile(self.tempfile, "/", "", "", None) as tar_file_obj:
      tar_file_obj.add_tree(self.data_files.Rlocation("rules_pkg/tests/testdata/"), "/")
    helper.assertTarFileContent(self, self.tempfile, [
        {"name": "./hello.txt", "data": "Hello, world!\n".encode("utf-8")},
        {"name": "subdir"},
        {"name": "./subdir"},
        {"name": "./subdir/world.txt", "data": "Hello, world!\n".encode("utf-8")},
    ])


if __name__ == "__main__":
  unittest.main()
