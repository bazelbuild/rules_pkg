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
"""expand_yml.py - read .yml and dump as json.

This is a debugging tool to expand a Yaml file and print the full expansion in
a more readable form.

Usage:
  python expand_ym.py [file ...]

  It no input files a provided, use tests.yml
"""

import json
import sys
import yaml


def show_expanded(path):
  with open(path, mode='r') as f:
    yml = yaml.load(f, Loader=yaml.FullLoader)
    print(json.dumps(yml, indent=2, sort_keys=True))


if __name__ == '__main__':
  if len(sys.argv) < 2:
    show_expanded('tests.yml')
  else:
    for f in sys.argv[1:]:
      show_expanded(f)
