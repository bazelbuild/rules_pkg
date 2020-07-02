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
"""Testing for archive."""

import os
import os.path
import tarfile
import unittest

PORTABLE_MTIME = 946684800  # 2000-01-01 00:00:00.000 UTC


class PkgTarTest(unittest.TestCase):
  """Testing for pkg_tar rule."""

  def assertTarFileContent(self, file_name, content):
    """Assert that tarfile contains exactly the entry described by `content`.

    Args:
        file_name: the path to the TAR file to test.
        content: an array describing the expected content of the TAR file.
            Each entry in that list should be a dictionary where each field
            is a field to test in the corresponding TarInfo. For
            testing the presence of a file "x", then the entry could simply
            be `{'name': 'x'}`, the missing field will be ignored. To match
            the content of a file entry, use the key 'data'.
    """
    file_path = os.path.join(os.environ['RUNFILES_DIR'], 'rules_pkg', 'tests', file_name)
    with tarfile.open(file_path, 'r:*') as f:
      i = 0
      for info in f:
        error_msg = 'Extraneous file at end of archive %s: %s' % (
            file_path,
            info.name
            )
        self.assertTrue(i < len(content), error_msg)
        for k, v in content[i].items():
          if k == 'data':
            value = f.extractfile(info).read()
          elif k == 'isdir':
            value = info.isdir()
          else:
            value = getattr(info, k)
          error_msg = ' '.join([
              'Value `%s` for key `%s` of file' % (value, k),
              '%s in archive %s does' % (info.name, file_path),
              'not match expected value `%s`' % v
              ])
          self.assertEqual(value, v, error_msg)
        i += 1
      if i < len(content):
        self.fail('Missing file %s in archive %s' % (content[i], file_path))

  def test_strip_prefix_empty(self):
    content = [
        {'name': '.'},
        {'name': './nsswitch.conf'},
    ]
    self.assertTarFileContent('test-tar-strip_prefix-empty.tar', content)

  def test_strip_prefix_none(self):
    content = [
        {'name': '.', 'isdir': True},
        {'name': './nsswitch.conf'},
    ]
    self.assertTarFileContent('test-tar-strip_prefix-none.tar', content)

  def test_strip_prefix_etc(self):
    content = [
        {'name': '.', 'isdir': True},
        {'name': './nsswitch.conf'},
    ]
    self.assertTarFileContent('test-tar-strip_prefix-etc.tar', content)

  def test_strip_prefix_dot(self):
    content = [
        {'name': '.'},
        {'name': './etc'},
        {'name': './etc/nsswitch.conf'},
        {'name': './external'},
        {'name': './external/bazel_tools'},
        {'name': './external/bazel_tools/tools'},
        {'name': './external/bazel_tools/tools/python'},
        {'name': './external/bazel_tools/tools/python/runfiles'},
        {'name': './external/bazel_tools/tools/python/runfiles/runfiles.py'},
    ]
    self.assertTarFileContent('test-tar-strip_prefix-dot.tar', content)

  def test_strip_files_dict(self):
    content = [
        {'name': '.'},
        {'name': './not-etc'},
        {'name': './not-etc/mapped-filename.conf'},
    ]
    self.assertTarFileContent('test-tar-files_dict.tar', content)

  def test_empty_files(self):
    content = [
        {'name': '.'},
        {'name': './a', 'size': 0, 'uid': 0},
        {'name': './b', 'size': 0, 'uid': 0, 'mtime': PORTABLE_MTIME},
    ]
    self.assertTarFileContent('test-tar-empty_files.tar', content)

  def test_empty_dirs(self):
    content = [
        {'name': '.'},
        {'name': './tmp', 'isdir': True, 'size': 0, 'uid': 0,
         'mtime': PORTABLE_MTIME },
        {'name': './pmt', 'isdir': True, 'size': 0, 'uid': 0,
         'mtime': PORTABLE_MTIME},
    ]
    self.assertTarFileContent('test-tar-empty_dirs.tar', content)

  def test_mtime(self):
    # Note strange mtime. It is specified in the BUILD file.
    content = [
        {'name': '.', 'mtime': 946684740},
        {'name': './nsswitch.conf', 'mtime': 946684740},
    ]
    self.assertTarFileContent('test-tar-mtime.tar', content)

  def test_basic(self):
    # Check the set of 'test-tar-basic-*' smoke test.
    content = [
        {'name': '.'},
        {'name': './etc',
         'uid': 24, 'gid': 42, 'uname': 'tata', 'gname': 'titi'},
        {'name': './etc/nsswitch.conf',
         'mode': 0o644,
         'uid': 24, 'gid': 42, 'uname': 'tata', 'gname': 'titi'
         },
        {'name': './usr',
         'uid': 42, 'gid': 24, 'uname': 'titi', 'gname': 'tata'},
        {'name': './usr/titi',
         'mode': 0o755,
         'uid': 42, 'gid': 24, 'uname': 'titi', 'gname': 'tata'},
        {'name': './usr/bin'},
        {'name': './usr/bin/java', 'linkname': '/path/to/bin/java'},
    ]
    for ext in ('', '.gz', '.bz2', '.xz'):
      with self.subTest(ext=ext):
        self.assertTarFileContent('test-tar-basic-%s.tar%s' % (ext[1:], ext),
                                  content)

  def test_file_inclusion(self):
    content = [
        {'name': '.'},
        {'name': './etc', 'uid': 24, 'gid': 42},
        {'name': './etc/nsswitch.conf', 'mode': 0o644, 'uid': 24, 'gid': 42},
        {'name': './usr', 'uid': 42, 'gid': 24},
        {'name': './usr/titi', 'mode': 0o755, 'uid': 42, 'gid': 24},
        {'name': './usr/bin'},
        {'name': './usr/bin/java', 'linkname': '/path/to/bin/java'},
    ]
    for ext in ('', '.gz', '.bz2', '.xz'):
      with self.subTest(ext=ext):
        self.assertTarFileContent('test-tar-inclusion-%s.tar' % ext[1:],
                                  content)


if __name__ == '__main__':
  unittest.main()
