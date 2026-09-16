# Copyright 2026 The Bazel Authors. All rights reserved.
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
#
# -*- coding: utf-8 -*-
"""Tests that pkg_deb computes Installed-Size automatically when unset."""

import unittest

from python.runfiles import runfiles
from tests.deb.pkg_deb_test import DebInspect


class PkgDebInstalledSizeTest(unittest.TestCase):
  """Testing automatic Installed-Size computation for pkg_deb."""

  def setUp(self):
    super(PkgDebInstalledSizeTest, self).setUp()
    self.runfiles = runfiles.Create()
    self.deb_path = self.runfiles.Rlocation(
        'rules_pkg/tests/deb/fizzbuzz-noinstsize_1.0_all.deb')
    self.deb_file = DebInspect(self.deb_path)

  def test_installed_size_is_computed(self):
    control = self.deb_file.get_deb_ctl_file('control')
    # :tar_input contains "etc/nsswitch.conf\n" (19 bytes) and
    # "usr/fizzbuzz\n" (13 bytes), for 32 bytes total, rounded up to 1 KiB.
    self.assertIn('Installed-Size: 1\n', control)


if __name__ == '__main__':
  unittest.main()
