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
import stat
import subprocess

from rules_python.python.runfiles import runfiles
from private.manifest import ENTRY_IS_FILE, ENTRY_IS_LINK, ENTRY_IS_DIR, ManifestEntry, entry_type_to_string


class PkgInstallTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runfiles = runfiles.Create()
        # Somewhat of an implementation detail, but it works.  I think.
        manifest_file = cls.runfiles.Rlocation("rules_pkg/tests/install/test_installer_install_script-install-manifest.json")

        with open(manifest_file, 'r') as fh:
            manifest_data_raw = json.load(fh)
            cls.manifest_data = {}
            for entry in manifest_data_raw:
                entry_struct = ManifestEntry(*entry)
                cls.manifest_data[entry_struct.dest] = entry_struct
        cls.installdir = os.path.join(os.getenv("TEST_TMPDIR"), "installdir")
        env = {}
        env.update(cls.runfiles.EnvVars())
        subprocess.check_call([
            cls.runfiles.Rlocation("rules_pkg/tests/install/test_installer"),
            "--destdir", cls.installdir,
            "--verbose",
        ],
                              env=env)

    def entity_type_at_path(self, path):
        if os.path.islink(path):
            return ENTRY_IS_LINK
        elif os.path.isfile(path):
            return ENTRY_IS_FILE
        elif os.path.isdir(path):
            return ENTRY_IS_DIR
        else:
            # We can't infer what TreeArtifacts are by looking at them -- the
            # build system is not aware of their contents.
            raise ValueError("Entity {} is not a link, file, or directory")

    def assertEntryTypeMatches(self, entry, actual_path):
        actual_entry_type = self.entity_type_at_path(actual_path)
        self.assertEqual(actual_entry_type, entry.entry_type,
                        "Entity {} should be a {}, but was actually {}".format(
                            entry.dest,
                            entry_type_to_string(entry.entry_type),
                            entry_type_to_string(actual_entry_type),
                        ))

    def assertEntryModeMatches(self, entry, actual_path):
        # TODO: permissions in windows are... tricky.  Don't bother
        # testing for them if we're in it for the time being
        if os.name == 'nt':
            return

        actual_mode = stat.S_IMODE(os.stat(actual_path).st_mode)
        expected_mode = int(entry.mode, 8)
        self.assertEqual(actual_mode, expected_mode,
                         "Entry {} has mode {:04o}, expected {:04o}".format(
                            entry.dest, actual_mode, expected_mode,
                        ))

    def test_manifest_matches(self):
        # TODO: check for ownership (user, group)
        found_entries = {dest: False for dest in self.manifest_data.keys()}
        for root, dirs, files in os.walk(self.installdir):
            rel_root_path = os.path.relpath(root, self.installdir)

            # TODO(nacl): check for treeartifacts here.  If so, prune `dirs`,
            # and set the rest aside for future processing.

            # Directory ownership tests
            if len(files) == 0 and len(dirs) == 0:
                # Empty directories must be explicitly requested by something
                if rel_root_path not in self.manifest_data:
                    self.fail("Directory {} not in manifest".format(rel_root_path))

                entry = self.manifest_data[rel_root_path]
                self.assertEntryTypeMatches(entry, root)
                self.assertEntryModeMatches(entry, root)

                found_entries[rel_root_path] = True
            else:
                # There's something in here.  Depending on how it was set up, it
                # could either be owned or unowned.
                if rel_root_path in self.manifest_data:
                    entry = self.manifest_data[rel_root_path]
                    self.assertEntryTypeMatches(entry, root)
                    self.assertEntryModeMatches(entry, root)

                    found_entries[rel_root_path] = True
                else:
                    print("{} is unowned".format(rel_root_path))

            for f in files:
                # The path on the filesystem in which the file actually exists.
                fpath = os.path.normpath("/".join([root, f]))
                # The path inside the manifest (relative to the install
                # destdir).
                rel_fpath = os.path.normpath("/".join([rel_root_path, f]))
                if rel_fpath not in self.manifest_data:
                    self.fail("Entity {} not in manifest".format(rel_fpath))

                entry = self.manifest_data[rel_fpath]
                self.assertEntryTypeMatches(entry, fpath)
                self.assertEntryModeMatches(entry, fpath)

                found_entries[rel_fpath] = True

        # TODO(nacl): check for TreeArtifacts

        num_missing = 0
        for dest, present in found_entries.items():
            if present is False:
                print("Entity {} is missing from the tree".format(dest))
                num_missing += 1
        self.assertEqual(num_missing, 0)


if __name__ == "__main__":
    unittest.main()
