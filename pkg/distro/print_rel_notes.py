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

import sys
from string import Template
import textwrap

from distro import release_tools


def print_notes(repo, version, tarball_path, org='bazelbuild'):
  file_name = release_tools.package_basename(repo, version)
  sha256 = release_tools.get_package_sha256(tarball_path)

  url = 'https://github.com/%s/%s/releases/download/%s/%s' % (
      org, repo, version, file_name)
  workspace_stanza = release_tools.workspace_content(url, repo, sha256)
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

      See [the source](https://github.com/${org}/${repo}/tree/master).
      ------------------------ snip ----------------------------

      """).strip())
  print(relnotes_template.substitute({
      'org': org,
      'repo': repo,
      'workspace_stanza': workspace_stanza,
  }))


def main(args):
  print_notes(repo=args[1], version=args[2], tarball_path=args[3])


if __name__ == '__main__':
  main(sys.argv)
