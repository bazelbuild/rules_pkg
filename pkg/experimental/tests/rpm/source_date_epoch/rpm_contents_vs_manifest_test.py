#!/usr/bin/env python3

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

import unittest
import csv
import io
import os
import rpm_util
from rules_python.python.runfiles import runfiles

# Tue Mar 23 00:00:00 EDT 2021
EXPECTED_EPOCH = '1616472000'
EXPECTED_RPM_MANIFEST_CSV = """
path,mtime
/test_dir/a,{epoch}
/test_dir/b,{epoch}
""".strip().format(epoch=EXPECTED_EPOCH)


class PkgRpmCompManifest(unittest.TestCase):
    def setUp(self):
        self.runfiles = runfiles.Create()
        self.maxDiff = None

        # TODO(nacl): make the other variants of this file consistent.  Consider
        # creating a base class.
        if "TEST_RPM" not in os.environ:
            self.fail("TEST_RPM must be set in the environment, containing the name of the RPM to test")

        # Allow for parameterization of this test based on the desired RPM to test.
        self.rpm_file_path = self.runfiles.Rlocation(os.path.join(
            os.environ["TEST_WORKSPACE"],
            "experimental", "tests", "rpm", "source_date_epoch",
            # The object behind os.environ is not a dict, and thus doesn't have
            # the "getdefault()" we'd otherwise use here.
            os.environ["TEST_RPM"],
        )) 

    def test_contents_match(self):
        sio = io.StringIO(EXPECTED_RPM_MANIFEST_CSV)
        manifest_reader = csv.DictReader(sio)
        manifest_specs = {r['path']: r for r in manifest_reader}

        rpm_specs = rpm_util.read_rpm_filedata(
            self.rpm_file_path,
            query_tag_map={
                "FILENAMES": "path",
                "FILEMTIMES": "mtime",
            })

        self.assertDictEqual(manifest_specs, rpm_specs)

    # Test if the RPM build time field is set to the provided SOURCE_DATE_EPOCH.
    def test_buildtime_set(self):
        actual_epoch = rpm_util.invoke_rpm_with_queryformat(self.rpm_file_path, "%{BUILDTIME}")
        self.assertEqual(actual_epoch, EXPECTED_EPOCH)

if __name__ == "__main__":
    unittest.main()
