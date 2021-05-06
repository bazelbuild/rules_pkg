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
"""Test time stamping in pkg_tar"""

import tarfile
import time
import unittest

from bazel_tools.tools.python.runfiles import runfiles

# keep in sync with archive.py
PORTABLE_MTIME = 946684800  # 2000-01-01 00:00:00.000 UTC

class PkgTarTest(unittest.TestCase):
  """Testing for pkg_tar rule."""

  def assertTarFilesAreAlmostNew(self, file_name):
    """Assert that tarfile contains files with an mtime of roughly now.

    Args:
        file_name: the path to the TAR file to test.
    """
    file_path = runfiles.Create().Rlocation('rules_pkg/tests/' + file_name)
    target_mtime = int(time.time())
    with tarfile.open(file_path, 'r:*') as f:
      i = 0
      for info in f:
        if info.mtime == PORTABLE_MTIME:
           self.fail('Archive %s contains file %s with portable mtime' % (
               file_path, info.name))
        if ((info.mtime < target_mtime - 10000)
            or (info.mtime > target_mtime + 10000)):
           self.fail('Archive %s contains file %s with mtime:%d, expected:%d' % (
               file_path, info.name, info.mtime, target_mtime))


  def test_not_epoch_times(self):
    self.assertTarFilesAreAlmostNew('stamped_tar.tar')


if __name__ == '__main__':
  unittest.main()
