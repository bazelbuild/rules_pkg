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

import filecmp
import os
import unittest
from zipfile import ZipFile

from build_zip import parse_date, ZIP_EPOCH

HELLO_CRC = 2069210904
LOREM_CRC = 2178844372
EXECUTABLE_CRC = 342626072

class ZipTest(unittest.TestCase):
    def get_test_zip(self, zipfile):
        """Get the file path to a generated zip in the runfiles."""
        data_files = os.environ.get("TEST_SRCDIR").replace('/', os.path.sep)
        return os.path.join(data_files, "rules_pkg", "tests", zipfile)


class ZipContentsCase(ZipTest):
    """Use zipfile to check the contents of some generated zip files."""

    def assertZipFileContent(self, zipfile, content):
        """Assert that zipfile contains the entries described by content.

        Args:
            zipfile: the test-package-relative path to a zip file to test.
            content: an array of dictionaries containing a filename and crc
                     key, and optionally a timestamp key.
        """
        with ZipFile(self.get_test_zip(zipfile)) as f:
            infos = f.infolist()
            self.assertEqual(len(infos), len(content))

            for info, expected in zip(infos, content):
                self.assertEqual(info.filename, expected["filename"])
                self.assertEqual(info.CRC, expected["crc"])

                ts = parse_date(expected.get("timestamp", ZIP_EPOCH))
                self.assertEqual(info.date_time, ts)
                self.assertEqual(info.external_attr >> 16, expected.get("attr", 0o555))


    def testEmpty(self):
        self.assertZipFileContent("test_zip_empty.zip", [])

    def testBasic(self):
        self.assertZipFileContent(
            "test_zip_basic.zip",
            [
                {"filename": "hello.txt", "crc": HELLO_CRC},
                {"filename": "loremipsum.txt", "crc": LOREM_CRC},
            ],
        )

    def testTimestamp(self):
        self.assertZipFileContent(
            "test_zip_timestamp.zip",
            [
                {"filename": "hello.txt", "crc": HELLO_CRC, "timestamp": 1234567890},
            ],
        )

    def testPermissions(self):
        self.assertZipFileContent(
            "test_zip_permissions.zip",
            [
                { 
                    "filename": "executable.sh",
                    "crc": EXECUTABLE_CRC,
                    "timestamp": 1234567890,
                    "attr": 0o644,
                }
            ]
        )

    def testPackageDir(self):
        self.assertZipFileContent(
            "test_zip_package_dir0.zip",
            [
                {"filename": "abc/def/hello.txt", "crc": HELLO_CRC},
                {"filename": "abc/def/loremipsum.txt", "crc": LOREM_CRC},
            ],
        )


class ZipEquivalency(ZipTest):
    """Check that some generated zip files are equivalent to each-other."""

    def assertFilesEqual(self, actual, expected):
        """Assert that two zip files contain the same bytes."""

        zipsAreEqual = filecmp.cmp(
            self.get_test_zip(actual),
            self.get_test_zip(expected),
        )

        self.assertTrue(zipsAreEqual)

    def testSmallTimestamp(self):
        self.assertFilesEqual(
            "test_zip_basic_timestamp_before_epoch.zip",
            "test_zip_basic.zip",
        )

    def testExtension(self):
        self.assertFilesEqual(
            "test_zip_empty_different_extension.otherkindofzip",
            "test_zip_empty.zip",
        )

    def testPackageDir1(self):
        self.assertFilesEqual(
            "test_zip_package_dir1.zip",
            "test_zip_package_dir0.zip",
        )

    def testPackageDir2(self):
        self.assertFilesEqual(
            "test_zip_package_dir2.zip",
            "test_zip_package_dir0.zip",
        )

if __name__ == "__main__":
    unittest.main()
