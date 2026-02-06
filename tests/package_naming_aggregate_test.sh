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

# This test simply checks that when we create packages with package_file_name
# that we get the expected file names.
set -euo pipefail

# Minimalistic `rlocation`: https://github.com/bazelbuild/rules_shell/blob/main/shell/runfiles/runfiles.bash
locate() {
  if [ -n "${RUNFILES_MANIFEST_FILE:-}" ]; then
    grep -m1 "^$1 " "$RUNFILES_MANIFEST_FILE" | cut -d' ' -f2-
  else
    echo "$TEST_SRCDIR/$1"
  fi
}

# Portably find the absolute path to the test data, even if this code has been
# vendored in to a source tree and re-rooted.
TEST_PACKAGE="$(echo ${TEST_TARGET} | sed -e 's/:.*$//' -e 's@//@@')"

for pkg in test_naming_some_value.deb test_naming_some_value.tar test_naming_some_value.zip ; do
  ls -l "$(locate "$TEST_WORKSPACE/$TEST_PACKAGE/$pkg")"
done
echo "PASS"
