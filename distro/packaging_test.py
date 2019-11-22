# Copyright 2019 The Bazel Authors. All rights reserved.
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

"""Test that the rules_pkg distribution is usable."""

import os
import subprocess
import unittest

from bazel_tools.tools.python.runfiles import runfiles
from releasing import release_tools
from distro import release_version

_VERBOSE = True


class PackagingTest(unittest.TestCase):
  """Test the distribution packaging."""

  def setUp(self):
    self.data_files = runfiles.Create()
    self.repo = 'rules_pkg'
    self.version = release_version.RELEASE_VERSION

  def testBuild(self):
    # Set up a fresh Bazel workspace using the currently build repo.
    tempdir = os.path.join(os.environ['TEST_TMPDIR'], 'build')
    if not os.path.exists(tempdir):
      os.makedirs(tempdir)
    with open(os.path.join(tempdir, 'WORKSPACE'), 'w') as workspace:
      file_name = release_tools.package_basename(self.repo, self.version)
      local_path = runfiles.Create().Rlocation(
          os.path.join('rules_pkg', 'distro', file_name))
      sha256 = release_tools.get_package_sha256(local_path)
      workspace_content = '\n'.join((
        'workspace(name = "test_rules_pkg_packaging")',
        release_tools.workspace_content(
            'file://%s' % local_path, self.repo, sha256)
      ))
      workspace.write(workspace_content)
      if _VERBOSE:
        print('=== WORKSPACE ===')
        print(workspace_content)

    # We do a little dance of renaming *.tmpl to *, mostly so that we do not
    # have a BUILD file in testdata, which would create a package boundary.
    def CopyTestFile(source_name, dest_name):
      source_path = self.data_files.Rlocation(
          os.path.join('rules_pkg', 'distro', 'testdata', source_name))
      with open(source_path) as inp:
        with open(os.path.join(tempdir, dest_name), 'w') as out:
          content = inp.read()
          out.write(content)

    CopyTestFile('BUILD.tmpl', 'BUILD')

    os.chdir(tempdir)
    build_result = subprocess.check_output(['bazel', 'build', ':dummy_tar'])
    if _VERBOSE:
      print('=== Build Result ===')
      print(build_result)

    content = subprocess.check_output(
        ['/bin/tar', 'tzf', 'bazel-bin/dummy_tar.tar.gz'])
    self.assertEqual(b'./\n./BUILD\n', content)


if __name__ == '__main__':
  unittest.main()
