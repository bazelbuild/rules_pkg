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
from string import Template
import textwrap

WORKSPACE_STANZA = (
"""
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
http_archive(
    name = "${repo}",
    url = "${url}",
    sha256 = "${sha256}",
)
%s
""")

DEPS_STANZA = (
"""
load("@${repo}//:deps.bzl", "${repo}_dependencies")
${repo}_dependencies()
""")

def package_basename(repo, version):
  return '%s-%s.tar.gz' % (repo, version)


def get_package_sha256(tarball_path):
  with open(tarball_path, 'rb') as pkg_content:
    tar_sha256 = hashlib.sha256(pkg_content.read()).hexdigest()
  return tar_sha256


def workspace_content(url, repo, sha256, has_deps_file=True):
  # Set up a fresh Bazel workspace
  deps = DEPS_STANZA if has_deps_file else ""
  workspace_stanza_template = Template((WORKSPACE_STANZA % deps).strip())
  return workspace_stanza_template.substitute({
      'url': url,
      'sha256': sha256,
      'repo': repo,
  })
