# Copyright 2026 The Bazel Authors. All rights reserved.
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
"""Helpers for using runfiles in tests."""

import os


def rlocation(runfiles, path):
  """Like runfiles.Rlocation(path), but the result can be opened on Windows.

  With --enable_runfiles on Windows, Bazel may create a directory junction
  for a file runfile. Such a junction can not be opened or executed, and
  os.path.realpath fails on it, so we read the junction target instead.

  Args:
    runfiles: A runfiles object, from runfiles.Create().
    path: The runfiles path to look up.
  Returns:
    The location of path, with a Windows junction replaced by its target.
  """
  location = runfiles.Rlocation(path)
  if os.name != "nt":
    return location
  try:
    target = os.readlink(location)
  except OSError:
    # Not a link.
    return location
  if target.startswith("\\\\?\\"):
    target = target[4:]
  return os.path.join(os.path.dirname(location), target)
