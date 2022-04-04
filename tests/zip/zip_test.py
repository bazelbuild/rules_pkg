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
from tests.zip import zip_test_lib

HELLO_CRC = 2069210904
LOREM_CRC = 2178844372
EXECUTABLE_CRC = 342626072


class ZipContentsTests(zip_test_lib.ZipContentsTestBase):

  def test_empty(self):
    self.assertZipFileContent("test_zip_empty.zip", [])

  def test_basic(self):
    self.assertZipFileContent("test_zip_basic.zip", [
        {"filename": "foodir/", "isdir": True, "attr": 0o711},
        {"filename": "hello.txt", "crc": HELLO_CRC},
        {"filename": "loremipsum.txt", "crc": LOREM_CRC},
        {"filename": "usr/bin/foo", "attr": 0o555, "data": "/usr/local/foo/foo.real"},
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

  def test_zip_tree(self):
    self.assertZipFileContent("test_zip_tree.zip", [
        {"filename": "generate_tree/a/a"},
        {"filename": "generate_tree/a/b/c"},
        {"filename": "generate_tree/b/c/d"},
        {"filename": "generate_tree/b/d"},
        {"filename": "generate_tree/b/e"},
    ])


if __name__ == "__main__":
  unittest.main()
