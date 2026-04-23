# Copyright 2024 The Bazel Authors. All rights reserved.
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
"""Tests that package_variables substitution works in pkg_deb string attributes."""

import codecs
from io import BytesIO
import tarfile
import unittest

from python.runfiles import runfiles
from pkg.private import archive


class DebInspect(object):
    """Class to open and unpack a .deb file so we can examine it."""

    def __init__(self, deb_file):
        self.deb_version = None
        self.data = None
        self.control = None
        with archive.SimpleArReader(deb_file) as f:
            info = f.next()
            while info:
                if info.filename == "debian-binary":
                    self.deb_version = info.data
                elif info.filename == "control.tar.gz":
                    self.control = info.data
                elif info.filename == "data.tar.gz":
                    self.data = info.data
                else:
                    raise Exception("Unexpected file: %s" % info.filename)
                info = f.next()

    def get_deb_ctl_file(self, file_name):
        """Extract a control file."""
        with tarfile.open(mode="r:gz", fileobj=BytesIO(self.control)) as f:
            for info in f:
                if info.name == "./" + file_name:
                    return codecs.decode(f.extractfile(info).read(), "utf-8")
        raise Exception("Could not find control file: %s" % file_name)


class PkgDebVariablesTest(unittest.TestCase):
    """Tests that package_variables substitution is applied to pkg_deb string attributes."""

    def setUp(self):
        super(PkgDebVariablesTest, self).setUp()
        self.runfiles = runfiles.Create()
        # my_package_variables provides arch=target_arch, label="some_value", so:
        #   package = "pkg-$(label)" -> "pkg-some_value"
        #   architecture = "$(arch)" -> "target_arch"
        deb_path = self.runfiles.Rlocation(
            "rules_pkg/tests/deb/pkg-some_value_1.0_target_arch.deb"
        )
        self.deb_file = DebInspect(deb_path)

    def test_control_fields_have_substituted_values(self):
        control = self.deb_file.get_deb_ctl_file("control")
        # Variables from my_package_variables: label="some_value"
        fields_expected = [
            "Package: pkg-some_value",
            "Architecture: target_arch",
            "Depends: dep-some_value",
        ]
        for field in fields_expected:
            self.assertIn(
                field,
                control,
                "Missing or unsubstituted control field: <%s> in <%s>"
                % (field, control),
            )

    def test_description_has_substituted_value(self):
        control = self.deb_file.get_deb_ctl_file("control")
        self.assertIn(
            "Description: Description for some_value",
            control,
            "Description field does not have substituted value in <%s>" % control,
        )
        # Confirm the raw variable syntax is NOT present
        self.assertNotIn(
            "$(label)",
            control,
            "Raw variable syntax still present in control: <%s>" % control,
        )


if __name__ == "__main__":
    unittest.main()
