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

import datetime
import filecmp
import unittest
import zipfile

from bazel_tools.tools.python.runfiles import runfiles

HELLO_CRC = 2069210904
LOREM_CRC = 2178844372
EXECUTABLE_CRC = 342626072

# Unix dir bit and Windows dir bit. Magic from zip spec
UNIX_DIR_BIT = 0o40000
MSDOS_DIR_BIT = 0x10

# The ZIP epoch date: (1980, 1, 1, 0, 0, 0)
_ZIP_EPOCH_DT = datetime.datetime(1980, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
_ZIP_EPOCH_S = int(_ZIP_EPOCH_DT.timestamp())

def seconds_to_ziptime(s):
  dt = datetime.datetime.utcfromtimestamp(s)
  return (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)


class ZipTest(unittest.TestCase):

  def get_test_zip(self, zip_file):
    """Get the file path to a generated zip in the runfiles."""

    return self.data_files.Rlocation(
        "rules_pkg/tests/zip/" + zip_file
    )

  def setUp(self):
    super(ZipTest, self).setUp()
    self.data_files = runfiles.Create()


class ZipContentsCase(ZipTest):
  """Use zipfile to check the contents of some generated zip files."""

  def assertZipFileContent(self, zip_file, content):
    """Assert that zip_file contains the entries described by content.

    Args:
        zip_file: the test-package-relative path to a zip file to test.
        content: an array of dictionaries containing a filename and crc key,
                 and optionally a timestamp key.
    """
    with zipfile.ZipFile(self.get_test_zip(zip_file)) as f:
      infos = f.infolist()
      self.assertEqual(len(infos), len(content))

      for info, expected in zip(infos, content):
        self.assertEqual(info.filename, expected["filename"])
        if "crc" in expected:
          self.assertEqual(info.CRC, expected["crc"])

        ts = seconds_to_ziptime(expected.get("timestamp", _ZIP_EPOCH_S))
        self.assertEqual(info.date_time, ts)
        if "isdir" in expected:
          expect_dir_bits = UNIX_DIR_BIT << 16 | MSDOS_DIR_BIT
          self.assertEqual(info.external_attr & expect_dir_bits,
                           expect_dir_bits)
        self.assertEqual(info.external_attr >> 16 & ~UNIX_DIR_BIT,
                         expected.get("attr", 0o555))

  def test_empty(self):
    self.assertZipFileContent("test_zip_empty.zip", [])

  def test_basic(self):
    self.assertZipFileContent("test_zip_basic.zip", [
        {"filename": "foodir/", "isdir": True, "attr": 0o711},
        {"filename": "hello.txt", "crc": HELLO_CRC},
        {"filename": "loremipsum.txt", "crc": LOREM_CRC},
    ])

  def test_timestamp(self):
    self.assertZipFileContent("test_zip_timestamp.zip", [
        {"filename": "hello.txt", "crc": HELLO_CRC, "timestamp": 1234567890},
    ])

  def test_permissions(self):
    self.assertZipFileContent("test_zip_permissions.zip", [
        {
            "filename": "executable.sh",
            "crc": EXECUTABLE_CRC,
            "timestamp": 1234567890,
            "attr": 0o644,
        }
    ])

  def test_package_dir(self):
    self.assertZipFileContent("test_zip_package_dir0.zip", [
        {"filename": "abc/def/hello.txt", "crc": HELLO_CRC},
        {"filename": "abc/def/loremipsum.txt", "crc": LOREM_CRC},
    ])

  def test_zip_strip_prefix_empty(self):
    self.assertZipFileContent("test-zip-strip_prefix-empty.zip", [
        {"filename": "loremipsum.txt", "crc": LOREM_CRC},
    ])

  def test_zip_strip_prefix_none(self):
    self.assertZipFileContent("test-zip-strip_prefix-none.zip", [
        {"filename": "loremipsum.txt", "crc": LOREM_CRC},
    ])

  def test_zip_strip_prefix_zipcontent(self):
    self.assertZipFileContent("test-zip-strip_prefix-zipcontent.zip", [
        {"filename": "loremipsum.txt", "crc": LOREM_CRC},
    ])

  def test_zip_strip_prefix_dot(self):
    self.assertZipFileContent("test-zip-strip_prefix-dot.zip", [
        {"filename": "zipcontent/loremipsum.txt", "crc": LOREM_CRC},
    ])


class ZipEquivalency(ZipTest):
  """Check that some generated zip files are equivalent to each-other."""

  def assertFilesEqual(self, actual, expected):
    """Assert that two zip files contain the same bytes."""

    zips_are_equal = filecmp.cmp(
        self.get_test_zip(actual),
        self.get_test_zip(expected),
    )
    self.assertTrue(zips_are_equal)

  def test_small_timestamp(self):
    self.assertFilesEqual(
        "test_zip_basic_timestamp_before_epoch.zip",
        "test_zip_basic.zip",
    )

  def test_extension(self):
    self.assertFilesEqual(
        "test_zip_empty_different_extension.otherkindofzip",
        "test_zip_empty.zip",
    )

  def test_package_dir1(self):
    self.assertFilesEqual(
        "test_zip_package_dir1.zip",
        "test_zip_package_dir0.zip",
    )

  def test_package_dir2(self):
    self.assertFilesEqual(
        "test_zip_package_dir2.zip",
        "test_zip_package_dir0.zip",
    )

if __name__ == "__main__":
  unittest.main()
