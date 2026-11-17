#!/usr/bin/env python3

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

import os
import subprocess
import unittest

from python.runfiles import runfiles


def _auto_dependencies(env_var):
    rpm_path = runfiles.Create().Rlocation(os.environ[env_var])
    output = subprocess.check_output([
        "rpm", "-qp", "--queryformat",
        "[%{REQUIRENEVRS} %{REQUIREFLAGS:deptype}\n]"
        "[%{PROVIDENEVRS} %{PROVIDEFLAGS:deptype}\n]",
        rpm_path,
    ]).decode("utf-8")
    return [line for line in output.splitlines() if line.endswith(" auto")]


class PkgRpmAutoReqProvTest(unittest.TestCase):
    def test_default_generates_dependencies(self):
        self.assertNotEqual(_auto_dependencies("TEST_RPM_AUTOREQPROV"), [])

    def test_disabled_generates_no_dependencies(self):
        self.assertEqual(_auto_dependencies("TEST_RPM_NO_AUTOREQPROV"), [])


if __name__ == "__main__":
    unittest.main()
