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
"""Print release notes for the package.

"""

import sys
import textwrap

from bazel_tools.tools.python.runfiles import runfiles
from distro import release_tools
from distro import release_version


def print_notes(version):
  file_name = release_tools.package_basename(version)
  _, sha256 = release_tools.get_package_info(version)

  url = 'https://github.com/bazelbuild/rules_pkg/releases/download/%s/%s' % (
      version, file_name)
  print(textwrap.dedent(
      """

      **WORKSPACE setup**

      ```
      """).strip())
  print(release_tools.workspace_content(url, sha256))
  print(textwrap.dedent(
      """
      ```

      **Using the rules**

      See [the source](https://github.com/bazelbuild/rules_pkg/tree/master/pkg).
      """).strip())


def main(_):
  print_notes(release_version.RELEASE_VERSION)


if __name__ == '__main__':
  main(sys.argv)
