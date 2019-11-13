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
"""Print release notes for a package.

"""

import argparse
import sys
from string import Template
import textwrap

from releasing import release_tools


def print_notes(org, repo, version, tarball_path, setup_file=None,
                deps_method=None, toolchains_method=None):
  file_name = release_tools.package_basename(repo, version)
  sha256 = release_tools.get_package_sha256(tarball_path)

  url = 'https://github.com/%s/%s/releases/download/%s/%s' % (
      org, repo, version, file_name)
  workspace_stanza = release_tools.workspace_content(
      url, repo, sha256, setup_file=setup_file, deps_method=deps_method,
      toolchains_method=toolchains_method)
  relnotes_template = Template(textwrap.dedent(
      """
      ------------------------ snip ----------------------------
      **New Features**

      **Incompatible Changes**

      **WORKSPACE setup**

      ```
      ${workspace_stanza}
      ```

      **Using the rules**

      See [the source](https://github.com/${org}/${repo}/tree/${version}).
      ------------------------ snip ----------------------------

      """).strip())
  print(relnotes_template.substitute({
      'org': org,
      'repo': repo,
      'version': version,
      'workspace_stanza': workspace_stanza,
  }))


def main():
  parser = argparse.ArgumentParser(
      description='Print release notes for a package')

  parser.add_argument(
      '--org', default='bazelbuild', help='Github org name')
  parser.add_argument(
      '--repo', default=None, required=True, help='Repo name')
  parser.add_argument(
      '--version', default=None, required=True, help='Release version')
  parser.add_argument(
      '--tarball_path', default=None,
      required=True, help='path to release tarball')
  parser.add_argument(
      '--setup_file', default=None,
      help='Alternate name for setup file. Default: deps.bzl')
  parser.add_argument(
      '--deps_method', default=None,
      help='Alternate name for dependencies method. Default: {repo}_dependencies')
  parser.add_argument(
      '--toolchains_method', default=None,
      help='Alternate name for toolchains method. Default: {repo}_toolchains')

  options = parser.parse_args()
  print_notes(options.org, options.repo, options.version, options.tarball_path,
              setup_file=options.setup_file, deps_method=options.deps_method,
              toolchains_method=options.toolchains_method)


if __name__ == '__main__':
  main()
