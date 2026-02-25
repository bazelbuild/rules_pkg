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
"""Workspace status file utilities."""

def get_status_vars(status_file, include_empty=True):
  result = {}
  with open(status_file, 'r') as f:
    for line in f:
      if not line.strip():
        continue
      parts = line.strip().split(' ', 1)
      if len(parts) == 2:
        result[parts[0]] = parts[1]
      elif include_empty:
        result[parts[0]] = ""

  return result

def get_timestamp(volatile_status_file):
  """Get BUILD_TIMESTAMP as an integer.

  Reads a file of "name<space>value" pairs and returns the value
  of the BUILD_TIMESTAMP. The file should be in the workspace status
  format: https://docs.bazel.build/versions/master/user-manual.html#workspace_status

  Args:
    volatile_status_file: path to input file. Typically ctx.version_file.path.
  Returns:
    int: value of BUILD_TIMESTAMP
  Exceptions:
    Exception: Raised if there is no BUILD_TIMESTAMP or if it is not a number.
  """
  status_vars = get_status_vars(volatile_status_file, include_empty=False)
  key = 'BUILD_TIMESTAMP'
  ts = status_vars.get(key)
  if ts is not None:
    return int(ts)
  raise Exception(
      "Invalid status file <%s>. Expected to find %s" % (volatile_status_file, key))
