#!/usr/bin/env python3

# Copyright 2020 The Bazel Authors. All rights reserved.
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

import itertools
import os
import sys
import unittest

# Global state used in the below test
files = []
mkdirs = []
links = []

# Rule stubs
def pkg_filegroup(**kwargs):
    global files
    files.append(kwargs)

def pkg_mkdirs(**kwargs):
    global mkdirs
    mkdirs.append(kwargs)

def pkg_mklinks(**kwargs):
    global links
    links.append(kwargs)

# Failure stub
class StarlarkException(Exception):
    pass
def fail(msg, **kwargs):
    raise StarlarkException(msg)

# "load" stub
def load(name, *args):
    pass

# Evaluate the manifest generating code with the above functions known
#
# This tosses a bunch of stuff into the global namespace, which isn't exactly clean.
#
# It also means that this test must be run sequentially.  Given how fast this
# will run, I'm not too concerned.
with open("experimental/manifest/manifest.bzl", "r") as fh:
    s = fh.read()
    exec(s)


# Here's an alternate way to do this "modularly".
#
# You'll also need to add all of the pkg_* functions above into the manifest_bzl
# module.  To be truly self-contained, this may need to be done inside the test case

#import importlib
#import builtins
#builtins.load = load
#spec = importlib.util.spec_from_loader("manifest_bzl",
#                                       importlib.machinery.SourceFileLoader("manifest_bzl", "experimental/manifest/manifest.bzl"))
#manifest_bzl = importlib.util.module_from_spec(spec)
#spec.loader.exec_module(manifest_bzl)

class PkgManifestTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        global files, mkdirs, links
        files.clear()
        mkdirs.clear()
        links.clear()

    @staticmethod
    def _manifest_fmt(name, idx):
        return "{}_manifest_elem_{}".format(name, idx)

    def test_copy_action(self):
        global files

        manifest = [
            ("/foo/baz/", "copy", "unix=0755;user=user;group=group", "foo:bar"),
        ]

        pkg_list_manifest(
            name = "manifest_copy",
            manifest = manifest,
            visibility = ["//visibility:public"]
        )

        # Only one item in the manifest
        self.assertEqual(len(files), 1)

        manifest_file = files[0]

        # Named properly
        self.assertEqual(manifest_file['name'], self._manifest_fmt("manifest_copy", 0))

        # Only one source (which is ["foo:bar"])
        self.assertListEqual(manifest_file['srcs'], ["foo:bar"])

        # Renaming operation -- which does not use a prefix
        self.assertEqual(manifest_file['prefix'], '/foo/baz/')
        self.assertIsNone(manifest_file['renames'])

        # Assert permissions propagated properly
        self.assertDictEqual(manifest_file['attrs'], {"unix": ["0755", "user", "group"]})

        # Assert kwargs propagated
        self.assertListEqual(manifest_file['visibility'], ['//visibility:public'])

    def test_copy_action_rename(self):
        global files

        manifest = [
            # Renaming
            ("/foo/baz", "copy", "unix=0755;user=user;group=group", "foo:bar"),
        ]

        pkg_list_manifest(
            name = "manifest_rename",
            manifest = manifest,
            visibility = ["//visibility:public"]
        )

        # Only one item in the manifest
        self.assertEqual(len(files), 1)

        manifest_file = files[0]

        # Named properly
        self.assertEqual(manifest_file['name'], self._manifest_fmt("manifest_rename", 0))

        # Only one source (which is ["foo:bar"])
        self.assertListEqual(manifest_file['srcs'], ["foo:bar"])

        # Renaming operation -- which does not use a prefix
        self.assertIsNone(manifest_file['prefix'])
        self.assertDictEqual(manifest_file['renames'], {"foo:bar": "/foo/baz"})

        # Assert permissions propagated properly
        self.assertDictEqual(manifest_file['attrs'], {"unix": ["0755", "user", "group"]})

        # Assert kwargs propagated
        self.assertListEqual(manifest_file['visibility'], ['//visibility:public'])

    def test_mkdir_action(self):
        global mkdirs
        manifest = [
            ("/foo/bar/qux", "mkdir", "unix=0777;user=user;group=group", "IGNORED"),
        ]

        pkg_list_manifest(
            name = "manifest_mkdir_single",
            manifest = manifest,
            visibility = ["//visibility:public"]
        )

        self.assertEqual(len(mkdirs), 1)

        manifest_dir = mkdirs[0]

        self.assertEqual(manifest_dir['name'], self._manifest_fmt("manifest_mkdir_single", 0))

        self.assertListEqual(manifest_dir['dirs'], ['/foo/bar/qux'])

        # Assert permissions propagated properly
        self.assertDictEqual(manifest_dir['attrs'], {"unix": ["0777", "user", "group"]})

        # Assert kwargs propagated
        self.assertListEqual(manifest_dir['visibility'], ['//visibility:public'])


    # TODO: the below skipped test
    def test_symlink_action(self):
        # Make a symlink, confirm whether or not its properties propagate properly
        self.skipTest("Not implemented")

    def test_multi_manifest(self):
        global files, mkdirs, links

        # Make a "full" manifest, see if everything is sufficiently consistent
        manifest = [
            ("/foo/baz/",     "copy",    "unix=0755;user=user;group=group", "foo:bar"),
            ("/foo/baz",      "copy",    "unix=0755;user=user;group=group", "foo:bar"),
            ("/foo/bar/qux",  "mkdir",   "unix=0777;user=user;group=group", "IGNORED"),
            ("/symlink-dest", "symlink", "user=user;group=group",           "/symlink-src")
        ]

        pkg_list_manifest(
            name = "manifest_multi",
            manifest = manifest,
        )

        self.assertEqual(len(files), 2)
        self.assertEqual(len(mkdirs), 1)
        self.assertEqual(len(links), 1)
        # print(files)
        # print(mkdirs)
        # print(links)

        for i, f in enumerate(files):
            expected_name = self._manifest_fmt("manifest_multi", i)
            self.assertEqual(f['name'], expected_name)
            # See if this field looks like a pkg_filegroup
            self.assertIn('prefix', f,
                          "copy action '{}' may not be correct (expected 'prefix' attribute)".format(expected_name))
            self.assertIn('renames', f,
                          "copy action '{}' may not be correct (expected 'renames' attribute)".format(expected_name))

        for i, d in enumerate(mkdirs, start=2):
            expected_name = self._manifest_fmt("manifest_multi", i)
            self.assertEqual(d['name'], expected_name)
            # See if this field looks like a pkg_mkdirs
            self.assertIn('dirs', d,
                          "directory action '{}' may not be correct (expected 'dirs' attribute)".format(expected_name))

        for i, l in enumerate(links, start=3):
            expected_name = self._manifest_fmt("manifest_multi", i)
            self.assertEqual(l['name'], expected_name)
            # See if this field looks like a pkg_mkdirs
            self.assertIn('links', l,
                          "symlink action '{}' may not be correct (expected 'links' attribute)".format(expected_name))

    def test_multi_manifest_with_defaults(self):
        # Like the above test, except try layering in some defaults
        global files, mkdirs, links

        # Make a "full" manifest, see if everything is sufficiently consistent
        manifest = [
            ("/foo/baz/",     "copy",    "user=user;group=group", "foo:bar"),
            ("/foo/baz",      "copy",    "user=user;group=group", "foo:bar"),
            ("/foo/bar/qux",  "mkdir",   "user=user;group=group", "IGNORED"),
            ("/symlink-dest", "symlink", "user=user;group=group", "/symlink-src")
        ]

        pkg_list_manifest(
            name = "manifest_multi",
            manifest = manifest,
            default_attrs = "unix=0755;user=root;group=root",
        )

        for idx, entry in enumerate(itertools.chain(files, mkdirs, links)):
            # user/group are overridden in each entry, but the permissions
            # aren't
            self.assertDictEqual(entry['attrs'], {"unix": ["0755", "user", "group"]},
                                 "Attrs for manifest entry {} are incorrect".format(idx))

    # TODO: the below skipped tests:
    def test_invalid_manifest(self):
        # Try passing in a manifest of improper size.  See if it's rejected
        # Pass in a manifest with an invalid action
        self.skipTest("Not implemented")

    def test_invalid_attributes(self):
        # Like attribute "fake_attribute"
        self.skipTest("Not implemented")

if __name__ == '__main__':
    unittest.main()
