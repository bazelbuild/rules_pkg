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

import json
import os
import unittest
from pathlib import Path
from python.runfiles import runfiles

DIRECTORY_ROOT = "%DIRECTORY_ROOT%"
# This is JSON, which shouldn't have any triple quotes in it.
EXPECTED_STRUCTURE = """%EXPECTED_STRUCTURE%"""


class DirectoryStructureTest(unittest.TestCase):
    def setUp(self):
        self.runfiles = runfiles.Create()

    def test_directory_structure_matches_global(self):
        real_directory_root = Path(self.runfiles.Rlocation(
            (Path(os.environ["TEST_WORKSPACE"]) / DIRECTORY_ROOT).as_posix()
        ))

        # This may be a bazel bug -- shouldn't an empty directory be passed in
        # anyway?
        self.assertTrue(
            real_directory_root.is_dir(),
            "TreeArtifact root does not exist, is the input empty?",
        )

        expected_set = set(json.loads(EXPECTED_STRUCTURE))
        actual_set = set()
        for file_path in real_directory_root.rglob("*"):
            if file_path.is_file():
                actual_set.add(file_path.relative_to(real_directory_root).as_posix())

        self.assertEqual(
            expected_set,
            actual_set,
            "Directory structure mismatch"
        )


if __name__ == "__main__":
    unittest.main()
