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
"""Checks that our Python packages ship explicit __init__.py files.

This test runs with legacy_create_init = 0, so any package whose
__init__.py is not in the runfiles would be imported as an implicit
namespace package, which has no __file__.
"""

import importlib
import unittest


class ExplicitInitTest(unittest.TestCase):

    def test_packages_are_regular_packages(self):
        for name in ("pkg", "pkg.private", "pkg.private.deb", "pkg.private.tar"):
            with self.subTest(package=name):
                module = importlib.import_module(name)
                self.assertIsNotNone(
                    module.__file__,
                    "%s is a namespace package; add its __init__.py to srcs" % name,
                )


if __name__ == "__main__":
    unittest.main()
