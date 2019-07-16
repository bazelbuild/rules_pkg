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

import unittest
import tempfile
import helpers


class HelpersTestCase(unittest.TestCase):
    def test_getFlagValue_nonStripped(self):
        self.assertEqual(helpers.GetFlagValue('value ', strip=False), 'value ')

    def test_getFlagValue_Stripped(self):
        self.assertEqual(helpers.GetFlagValue('value ', strip=True), 'value')

    def test_getFlagValue_nonStripped_fromFile(self):
        with tempfile.NamedTemporaryFile() as f:
            f.write('value ')
            f.flush()
            self.assertEqual(helpers.GetFlagValue(
                '@{}'.format(f.name),
                strip=False), 'value ')

    def test_getFlagValue_Stripped_fromFile(self):
        with tempfile.NamedTemporaryFile() as f:
            f.write('value ')
            f.flush()
            self.assertEqual(helpers.GetFlagValue(
                '@{}'.format(f.name),
                strip=True), 'value')


if __name__ == "__main__":
    unittest.main()
