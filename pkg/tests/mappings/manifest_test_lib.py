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
"""Compare to content manifest files."""

import json
import unittest

from bazel_tools.tools.python.runfiles import runfiles

class ContentManifestTest(unittest.TestCase):
  """Test harness to see if we wrote the content manifest correctly."""

  run_files = runfiles.Create()

  def assertManifestsMatch(self, expected, got):
    """Check two manifest files for equality.

    Args:
        expected: The path to the content we expect.
        got: The path to the content we got.
    """
    e_file = ContentManifestTest.run_files.Rlocation(
        'rules_pkg/tests/mappings/' + expected)
    with open(e_file, mode='rb') as e_fp:
      expected = json.load(e_fp)
    g_file = ContentManifestTest.run_files.Rlocation(
        'rules_pkg/tests/mappings/' + got)
    with open(g_file, mode='rb') as g_fp:
      got = json.load(g_fp)
    self.assertEqual(expected, got)
