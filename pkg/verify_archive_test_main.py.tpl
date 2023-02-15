# Copyright 2023 The Bazel Authors. All rights reserved.
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
"""Tests for generated content manifest."""

import unittest

from pkg import verify_archive_test_lib

class ${TEST_NAME}(verify_archive_test_lib.VerifyArchiveTest):

  def setUp(self):
    super(${TEST_NAME}, self).setUp()
    self.scan_target('${TARGET}')

  def test_min_size(self):
    self.assertMinSize(${MIN_SIZE})

  def test_max_size(self):
    self.assertMaxSize(${MAX_SIZE})

  def test_must_contain(self):
    self.check_must_contain(${MUST_CONTAIN})

  def test_must_not_contain(self):
    self.check_must_not_contain(${MUST_NOT_CONTAIN})

  def test_must_not_contain(self):
    self.check_must_contain_regex(${MUST_CONTAIN_REGEX})

  def test_must_not_contain(self):
    self.check_must_not_contain_regex(${MUST_NOT_CONTAIN_REGEX})


if __name__ == '__main__':
  unittest.main()
