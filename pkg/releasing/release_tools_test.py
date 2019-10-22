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

import filecmp
import os
import unittest

import release_tools


class ReleaseToolsTest(unittest.TestCase):

  def test_workspace_content_full(self):
    content = release_tools.workspace_content(
        url='http://github.com',
        repo='foo-bar',
        sha256='@computed@',
        setup_file='my_setup.bzl',
        deps_method='my_deps',
        toolchains_method='my_tools')
    self.assertTrue(content.find(' name = "foo_bar",') > 0, content)
    self.assertTrue(content.find(
        '\nload("@foo_bar//:my_setup.bzl", "my_deps", "my_tools")\n') > 0,
        content)
    self.assertTrue(content.find('\nmy_deps()\n') > 0)
    self.assertTrue(content.find('\nmy_tools()\n') > 0, content)

  def test_workspace_content_notools(self):
    content = release_tools.workspace_content(
        url='http://github.com',
        repo='foo-bar',
        sha256='@computed@',
        setup_file='my_setup.bzl',
        deps_method='my_deps')
    self.assertTrue(content.find(
        '\nload("@foo_bar//:my_setup.bzl", "my_deps")\n') > 0,
        content)
    self.assertTrue(content.find('\nmy_deps()\n') > 0)
    self.assertTrue(content.find('\nmy_tools()\n') < 0)

  def test_workspace_content_nodeps(self):
    content = release_tools.workspace_content(
        url='http://github.com',
        repo='foo-bar',
        sha256='@computed@',
        setup_file='my_setup.bzl',
        toolchains_method='my_tools')
    self.assertTrue(content.find(
        '\nload("@foo_bar//:my_setup.bzl", "my_tools")\n') > 0,
        content)
    self.assertTrue(content.find('\nmy_deps()\n') < 0)
    self.assertTrue(content.find('\nmy_tools()\n') > 0)

  def test_workspace_content_minimal(self):
    content = release_tools.workspace_content(
        url='http://github.com',
        repo='foo-bar',
        sha256='@computed@')
    self.assertTrue(content.find('\nload("@foo_bar') < 0)


if __name__ == "__main__":
    unittest.main()
