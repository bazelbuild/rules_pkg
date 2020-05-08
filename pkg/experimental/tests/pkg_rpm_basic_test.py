#!/usr/bin/env python3

# Copyright 2020 The Bazel Authors. All rights reserved.
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

import unittest
import subprocess
import csv
import io
from rules_python.python.runfiles import runfiles

# This provides some tests for built RPMs, mostly by taking the built RPM and
# running rpm queries on it.
#
# Useful reading:
#
# - RPM queryformat documentation (shortish):
#   https://rpm.org/user_doc/query_format.html
#
# - In-depth RPM query documentation:
#   http://ftp.rpm.org/max-rpm/s1-rpm-query-parts.html
#
# - Specifically, about the --qf/--queryformat syntax:
#   http://ftp.rpm.org/max-rpm/s1-rpm-query-parts.html#S3-RPM-QUERY-QUERYFORMAT-OPTION
#
# - --queryformat tags list: http://ftp.rpm.org/max-rpm/ch-queryformat-tags.html
#
class PkgRpmBasicTest(unittest.TestCase):
    def setUp(self):
        self.runfiles = runfiles.Create()
        self.test_rpm_path = self.runfiles.Rlocation(
            "rules_pkg/experimental/tests/test_rpm.rpm")
        self.maxDiff = None

    def test_scriptlet_content(self):
        expected = b"""\
preinstall scriptlet (using /bin/sh):
echo pre
postinstall scriptlet (using /bin/sh):
echo post
preuninstall scriptlet (using /bin/sh):
echo preun
postuninstall scriptlet (using /bin/sh):
echo postun
"""

        output = subprocess.check_output(
            ["rpm", "-qp", "--scripts", self.test_rpm_path])

        self.assertEqual(output, expected)

    def test_basic_headers(self):
        fields = {
            "NAME": b"test_rpm",
            "VERSION": b"1.1.1",
            "RELEASE": b"2222",
            "ARCH": b"noarch",
            "GROUP": b"Unspecified",
            "SUMMARY": b"pkg_rpm test rpm summary",
        }
        for fieldname, expected in fields.items():
            output = subprocess.check_output([
                "rpm", "-qp", "--queryformat", "%{" + fieldname + "}",
                self.test_rpm_path
            ])

            self.assertEqual(
                output, expected,
                "RPM Tag {} does not match expected value".format(fieldname))

    def test_contents(self):
        self.manifest_file = self.runfiles.Rlocation(
            "rules_pkg/experimental/tests/manifest.txt")
        manifest_specs = {}
        with open(self.manifest_file, "r", newline='', encoding="utf-8") as fh:
            manifest_reader = csv.DictReader(fh)
            manifest_specs = {r['path']: r for r in manifest_reader}

        rpm_queryformat = (
            "[%{FILENAMES}"
            ",%{FILESIZES}"
            ",%{FILEDIGESTS}"
            ",%{FILEUSERNAME}"
            ",%{FILEGROUPNAME}"
            ",%{FILEMODES:octal}"
            ",%{FILEFLAGS:fflags}"
            ",%{FILELINKTOS}"
            "\n]"
        )

        rpm_queryformat_fieldnames = [
            "path",
            "size",
            "digest",
            "user",
            "group",
            "mode",
            "fflags",
            "symlink",
        ]

        rpm_output = subprocess.check_output(
            ["rpm", "-qp", "--queryformat", rpm_queryformat, self.test_rpm_path])

        sio = io.StringIO(rpm_output.decode('utf-8'))
        rpm_output_reader = csv.DictReader(
            sio, fieldnames=rpm_queryformat_fieldnames)
        for rpm_file_info in rpm_output_reader:
            my_path = rpm_file_info['path']
            self.assertIn(my_path, manifest_specs)
            self.assertDictEqual(manifest_specs[my_path], rpm_file_info)


if __name__ == "__main__":
    unittest.main()
