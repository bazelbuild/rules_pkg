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
"""Utilities to help create a rule set release."""

import hashlib
import os
import textwrap

from bazel_tools.tools.python.runfiles import runfiles


def package_basename(version):
  return 'rules_pkg-%s.tar.gz' % version


def get_package_info(version):
  tar_path = runfiles.Create().Rlocation(
      os.path.join('rules_pkg', 'distro', package_basename(version)))
  with open(tar_path, 'r') as pkg_content:
    tar_sha256 = hashlib.sha256(pkg_content.read()).hexdigest()
  return tar_path, tar_sha256


def workspace_content(url, sha256):
  # Set up a fresh Bazel workspace
  return textwrap.dedent(
      """
      load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
      http_archive(
          name = "rules_pkg",
          url = "%s",
          sha256 = "%s",
      )

      load("@rules_pkg//:deps.bzl", "rules_pkg_dependencies")
      rules_pkg_dependencies()
      """ % (url, sha256)).strip()


"""
    # We do a little dance of renaming *.tmpl to *, mostly so that we do not
    # have a BUILD file in testdata, which would create a package boundary.
    def CopyTestFile(source_name, dest_name):
      source_path = self.data_files.Rlocation(
          os.path.join('rules_pkg', 'distro', 'testdata', source_name))
      with open(source_path) as inp:
        with open(os.path.join(tempdir, dest_name), 'w') as out:
          content = inp.read()
          out.write(content)

    CopyTestFile('BUILD.tmpl', 'BUILD')

    os.chdir(tempdir)
    build_result = subprocess.check_output(['bazel', 'build', ':dummy_tar'])
    if _VERBOSE:
      print('=== Build Result ===')
      print(build_result)

    content = subprocess.check_output(
        ['/bin/tar', 'tzf', 'bazel-bin/dummy_tar.tar.gz'])
    self.assertEqual('./\n./BUILD\n', content)
"""
